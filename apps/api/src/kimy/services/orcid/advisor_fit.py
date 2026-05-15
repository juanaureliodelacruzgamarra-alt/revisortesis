"""Advisor-fit scoring.

Compares the embedding of a submission's title against every publication an
advisor has imported from ORCID, using pgvector cosine distance. The "fit
score" is the highest cosine similarity found; below ``orcid_advisor_fit_threshold``
we flag the assignment for coordinator review.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import bindparam, select
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.core.config import get_settings
from kimy.models.orcid_publication import OrcidPublication
from kimy.models.submission import Submission
from kimy.services.plagiarism.embedder import embed_texts

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FitResult:
    score: float                # best cosine similarity in [0, 1] (clipped)
    alert: bool                 # True when score < threshold
    closest_publication_title: str | None
    publications_checked: int


async def compute_fit(
    session: AsyncSession,
    *,
    submission_id: UUID,
    advisor_id: UUID,
) -> FitResult | None:
    """Score `submission_id` against `advisor_id`'s publications.

    Returns None when the advisor has no publications imported (we can't judge
    fit without data, and forcing an alert would be misleading).
    """
    submission = await session.get(Submission, submission_id)
    if submission is None:
        return None

    title = submission.title.strip()
    if not title:
        return None

    query_text = title
    if submission.chapter:
        query_text = f"{title} — {submission.chapter}"

    embeddings, _backend = embed_texts([query_text])
    query_vec = embeddings[0]

    # Use pgvector's cosine distance (<=>). similarity = 1 - distance, clipped.
    stmt = (
        select(
            OrcidPublication.id,
            OrcidPublication.title,
            (1 - OrcidPublication.embedding.cosine_distance(
                bindparam("query_vec", value=query_vec)
            )).label("similarity"),
        )
        .where(OrcidPublication.advisor_id == advisor_id)
        .order_by("similarity")  # ascending — pull worst first then we'll just pick best
    )
    rows = list((await session.execute(stmt)).all())
    if not rows:
        return None

    best = max(rows, key=lambda r: r.similarity or 0.0)
    score = max(0.0, min(1.0, float(best.similarity or 0.0)))

    threshold = get_settings().orcid_advisor_fit_threshold
    return FitResult(
        score=score,
        alert=score < threshold,
        closest_publication_title=best.title,
        publications_checked=len(rows),
    )


async def update_submission_fit(
    session: AsyncSession,
    *,
    submission_id: UUID,
    advisor_id: UUID | None,
) -> FitResult | None:
    """Recompute and persist fit fields on `submissions`."""
    submission = await session.get(Submission, submission_id)
    if submission is None:
        return None

    if advisor_id is None:
        submission.advisor_fit_score = None
        submission.advisor_fit_alert = False
        await session.commit()
        return None

    fit = await compute_fit(session, submission_id=submission_id, advisor_id=advisor_id)
    if fit is None:
        # Advisor without ORCID linkage — keep score null but don't alert.
        submission.advisor_fit_score = None
        submission.advisor_fit_alert = False
    else:
        submission.advisor_fit_score = fit.score
        submission.advisor_fit_alert = fit.alert
    await session.commit()
    return fit
