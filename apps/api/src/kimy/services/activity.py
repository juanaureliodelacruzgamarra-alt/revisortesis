"""Cheap activity feed for the coordinator dashboard.

We don't have an explicit events table yet — instead we synthesize an activity
stream by UNIONing a few recent rows from the existing tables. Switch to a
proper event log if/when the load justifies it (Phase 12+).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.submission import Submission
from kimy.models.submission_version import SubmissionVersion


@dataclass(slots=True)
class ActivityItem:
    kind: str                   # submission_created | version_uploaded | evaluation_completed
    occurred_at: datetime
    submission_id: str
    submission_title: str
    actor_name: str
    description: str


async def recent(
    session: AsyncSession, *, program_id: UUID | None = None, limit: int = 15
) -> list[ActivityItem]:
    out: list[ActivityItem] = []

    sub_stmt = (
        select(Submission)
        .options(selectinload(Submission.student))
        .order_by(Submission.created_at.desc())
        .limit(limit)
    )
    if program_id is not None:
        sub_stmt = sub_stmt.where(Submission.program_id == program_id)
    subs = list((await session.execute(sub_stmt)).scalars().all())
    for s in subs:
        out.append(
            ActivityItem(
                kind="submission_created",
                occurred_at=s.created_at,
                submission_id=str(s.id),
                submission_title=s.title,
                actor_name=s.student.full_name if s.student else "—",
                description=f"Nuevo avance creado por {s.student.full_name if s.student else 'estudiante'}",
            )
        )

    ver_stmt = (
        select(SubmissionVersion, Submission)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
        .options(selectinload(Submission.student))
        .order_by(SubmissionVersion.created_at.desc())
        .limit(limit)
    )
    if program_id is not None:
        ver_stmt = ver_stmt.where(Submission.program_id == program_id)
    for v, s in (await session.execute(ver_stmt)).all():
        out.append(
            ActivityItem(
                kind="version_uploaded",
                occurred_at=v.created_at,
                submission_id=str(s.id),
                submission_title=s.title,
                actor_name=s.student.full_name if s.student else "—",
                description=(
                    f"Versión v{v.version_number} subida — {v.parsing_status.value}"
                ),
            )
        )

    eval_stmt = (
        select(AIEvaluation, Submission)
        .join(SubmissionVersion, SubmissionVersion.id == AIEvaluation.version_id)
        .join(Submission, Submission.id == SubmissionVersion.submission_id)
        .options(selectinload(Submission.student))
        .order_by(AIEvaluation.created_at.desc())
        .limit(limit)
    )
    if program_id is not None:
        eval_stmt = eval_stmt.where(Submission.program_id == program_id)
    for ev, s in (await session.execute(eval_stmt)).all():
        out.append(
            ActivityItem(
                kind="evaluation_completed",
                occurred_at=ev.created_at,
                submission_id=str(s.id),
                submission_title=s.title,
                actor_name=f"Aurelio ({ev.backend})",
                description=(
                    f"Evaluación IA completada — {ev.total_percentage:.0f}% / "
                    f"{ev.decimal_grade:.1f}/20 — {len(ev.findings) if False else ''}"
                ).strip(" —"),
            )
        )

    out.sort(key=lambda i: i.occurred_at, reverse=True)
    return out[:limit]
