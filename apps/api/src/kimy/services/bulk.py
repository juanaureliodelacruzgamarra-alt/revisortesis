"""Bulk operations over a set of submissions.

Each helper returns per-submission outcomes so the caller can present a partial-
success report to the coordinator. None of these raise on the per-row failure
path — failures are captured in the response dict.

Operations:
- ``reprocess_ai``: re-enqueues the latest version of each submission through
  the AI pipeline (heuristic stub or real LLM, same as a fresh upload).
- ``set_status``: applies a SubmissionStatus to every submission.
- ``assign_advisor``: assigns the same advisor (or None) to every submission
  and recomputes the ORCID advisor-fit for each.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import VersionParsingStatus

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BulkOutcome:
    submission_id: UUID
    ok: bool
    detail: str


async def _load_submissions(
    session: AsyncSession, ids: list[UUID]
) -> list[Submission]:
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.program),
            selectinload(Submission.versions),
        )
        .where(Submission.id.in_(ids))
    )
    return list((await session.execute(stmt)).scalars().all())


async def reprocess_ai(
    session: AsyncSession, ids: list[UUID]
) -> list[BulkOutcome]:
    """Mark each submission's latest version as ``ai_queued`` and schedule the
    pipeline. We don't piggy-back on BackgroundTasks here so the same helper
    works from REST callers and (later) Celery beats.
    """
    from kimy.services.ai import pipeline as ai_pipeline
    from kimy.services.submissions import latest_version

    submissions = await _load_submissions(session, ids)
    out: list[BulkOutcome] = []
    to_run: list[UUID] = []
    for s in submissions:
        v = latest_version(s)
        if v is None:
            out.append(BulkOutcome(s.id, False, "submission has no version"))
            continue
        v.parsing_status = VersionParsingStatus.ai_queued
        v.parsing_error = None
        to_run.append(v.id)
        out.append(BulkOutcome(s.id, True, "queued"))
    await session.commit()

    # Fire pipeline runs concurrently. Each owns its own session so we don't
    # share state with the request scope.
    async def _safe_run(version_id: UUID) -> None:
        try:
            await ai_pipeline.run_for_version(version_id)
        except Exception:  # noqa: BLE001
            logger.exception("bulk reprocess crashed for version %s", version_id)

    if to_run:
        # Detach: spawn but don't await all here — return quickly. The frontend
        # polls submission status to know when each finishes.
        for vid in to_run:
            asyncio.create_task(_safe_run(vid))

    not_found = set(ids) - {s.id for s in submissions}
    for missing in not_found:
        out.append(BulkOutcome(missing, False, "submission not found"))
    return out


async def set_status(
    session: AsyncSession,
    ids: list[UUID],
    status: SubmissionStatus,
) -> list[BulkOutcome]:
    submissions = await _load_submissions(session, ids)
    out: list[BulkOutcome] = []
    for s in submissions:
        previous = s.status
        s.status = status
        out.append(
            BulkOutcome(
                s.id,
                True,
                f"status: {previous.value} → {status.value}",
            )
        )
    await session.commit()
    not_found = set(ids) - {s.id for s in submissions}
    for missing in not_found:
        out.append(BulkOutcome(missing, False, "submission not found"))
    return out


async def assign_advisor(
    session: AsyncSession,
    ids: list[UUID],
    advisor_id: UUID | None,
) -> list[BulkOutcome]:
    from kimy.services.orcid import advisor_fit

    submissions = await _load_submissions(session, ids)
    out: list[BulkOutcome] = []
    for s in submissions:
        s.advisor_id = advisor_id
    await session.commit()

    # Recompute fit after we know the assignment took effect.
    for s in submissions:
        try:
            fit = await advisor_fit.update_submission_fit(
                session, submission_id=s.id, advisor_id=advisor_id
            )
            score_msg = (
                f"fit {fit.score * 100:.0f}% (alert={fit.alert})"
                if fit is not None
                else "advisor has no ORCID publications"
            )
            out.append(BulkOutcome(s.id, True, score_msg))
        except Exception as exc:  # noqa: BLE001
            logger.exception("bulk fit recompute failed for %s", s.id)
            out.append(BulkOutcome(s.id, False, f"fit recompute failed: {exc}"))

    not_found = set(ids) - {s.id for s in submissions}
    for missing in not_found:
        out.append(BulkOutcome(missing, False, "submission not found"))
    return out
