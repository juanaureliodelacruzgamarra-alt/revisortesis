"""Intra-program plagiarism scanner.

Public entry point: ``scan_version`` — embeds every chunk of a given version,
persists chunks + embeddings, and runs a cosine-similarity search against
chunks from OTHER submissions in the same academic program. Matches above the
threshold are persisted in `plagiarism_matches` for advisor review.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.document_chunk import DocumentChunk
from kimy.models.plagiarism_match import (
    PlagiarismMatch,
    PlagiarismSource,
    PlagiarismStatus,
)
from kimy.models.submission import Submission
from kimy.models.submission_version import SubmissionVersion
from kimy.services import storage
from kimy.services.documents.extractor import extract
from kimy.services.plagiarism.chunker import chunk_document
from kimy.services.plagiarism.embedder import embed_texts

logger = logging.getLogger(__name__)


SIMILARITY_THRESHOLD = 0.85
"""Above this cosine similarity a chunk pair is reported as a potential match."""

# pgvector exposes cosine *distance* via the `<=>` operator (1 - similarity),
# so threshold_distance = 1 - SIMILARITY_THRESHOLD.
COSINE_DISTANCE_THRESHOLD = 1 - SIMILARITY_THRESHOLD


@dataclass(slots=True)
class MatchSummary:
    matched_version_id: UUID
    matched_student_name: str
    matched_submission_title: str
    best_similarity: float
    chunk_count: int


async def scan_version(
    session: AsyncSession, version_id: UUID
) -> tuple[list[MatchSummary], str]:
    """Scan a version against the rest of its program. Returns (summaries, embedder_name)."""
    version = await session.get(SubmissionVersion, version_id)
    if version is None:
        logger.warning("plagiarism: version %s not found", version_id)
        return [], "none"

    submission = await session.get(Submission, version.submission_id)
    if submission is None:
        return [], "none"

    # 1. Extract text and chunk it
    path = storage.resolve(version.storage_path)
    if not path.is_file():
        logger.warning("plagiarism: file missing for version %s", version_id)
        return [], "none"

    extracted = extract(version.original_filename, path.read_bytes(), version.mime_type)
    chunks = chunk_document(extracted)
    if not chunks:
        logger.info("plagiarism: no chunks produced for version %s", version_id)
        return [], "none"

    # 2. Embed
    vectors, embedder_name = embed_texts([c.text for c in chunks])

    # 3. Wipe any prior chunks for idempotency, then persist new ones
    await session.execute(
        delete(DocumentChunk).where(DocumentChunk.version_id == version_id)
    )
    await session.execute(
        delete(PlagiarismMatch).where(PlagiarismMatch.version_id == version_id)
    )
    await session.flush()

    persisted_chunks: list[DocumentChunk] = []
    for chunk, vec in zip(chunks, vectors, strict=False):
        row = DocumentChunk(
            version_id=version_id,
            chunk_index=chunk.chunk_index,
            section=chunk.section,
            text=chunk.text,
            char_count=chunk.char_count,
            embedding=vec,
        )
        session.add(row)
        persisted_chunks.append(row)
    await session.flush()

    # 4. Cosine search against chunks from OTHER submissions in the same program.
    matches_by_version: dict[UUID, list[PlagiarismMatch]] = {}

    for chunk_row in persisted_chunks:
        # pgvector cosine distance: 1 - cosine_similarity. Smaller is more similar.
        stmt = (
            select(
                DocumentChunk,
                DocumentChunk.embedding.cosine_distance(chunk_row.embedding).label(
                    "distance"
                ),
            )
            .join(SubmissionVersion, SubmissionVersion.id == DocumentChunk.version_id)
            .join(Submission, Submission.id == SubmissionVersion.submission_id)
            .where(
                Submission.program_id == submission.program_id,
                Submission.id != submission.id,  # exclude same submission (older versions)
                DocumentChunk.embedding.cosine_distance(chunk_row.embedding)
                <= COSINE_DISTANCE_THRESHOLD,
            )
            .order_by("distance")
            .limit(3)
        )
        result = await session.execute(stmt)
        for candidate, distance in result.all():
            similarity = float(1 - distance)
            match = PlagiarismMatch(
                version_id=version_id,
                matched_version_id=candidate.version_id,
                source_chunk_id=chunk_row.id,
                matched_chunk_id=candidate.id,
                similarity=similarity,
                source=PlagiarismSource.intra,
                status=PlagiarismStatus.pending,
            )
            session.add(match)
            matches_by_version.setdefault(candidate.version_id, []).append(match)

    await session.commit()

    if not matches_by_version:
        return [], embedder_name

    # 5. Build per-other-submission summaries with metadata.
    summaries: list[MatchSummary] = []
    for matched_vid, group in matches_by_version.items():
        other_version = await session.get(
            SubmissionVersion,
            matched_vid,
            options=[selectinload(SubmissionVersion.submission)],
        )
        if other_version is None:
            continue
        other_submission = await _load_submission_with_student(
            session, other_version.submission_id
        )
        if other_submission is None:
            continue
        best = max(m.similarity for m in group)
        summaries.append(
            MatchSummary(
                matched_version_id=matched_vid,
                matched_student_name=other_submission.student.full_name,
                matched_submission_title=other_submission.title,
                best_similarity=best,
                chunk_count=len(group),
            )
        )

    return summaries, embedder_name


async def _load_submission_with_student(
    session: AsyncSession, submission_id: UUID
) -> Submission | None:
    stmt = (
        select(Submission)
        .options(selectinload(Submission.student))
        .where(Submission.id == submission_id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def list_matches_for_version(
    session: AsyncSession, version_id: UUID
) -> list[dict[str, Any]]:
    """Return matches grouped by matched_version with chunk-level detail.

    The shape is designed for the API response (router-side mapping is trivial).
    """
    stmt = (
        select(PlagiarismMatch)
        .options(
            selectinload(PlagiarismMatch.source_chunk),
            selectinload(PlagiarismMatch.matched_chunk),
            selectinload(PlagiarismMatch.matched_version)
            .selectinload(SubmissionVersion.submission)
            .selectinload(Submission.student),
        )
        .where(PlagiarismMatch.version_id == version_id)
        .order_by(PlagiarismMatch.similarity.desc())
    )
    return list((await session.execute(stmt)).scalars().all())
