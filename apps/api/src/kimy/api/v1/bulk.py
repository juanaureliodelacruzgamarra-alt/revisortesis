"""Bulk operations and batch reports for coordinators/admins.

Two endpoints:
- ``POST /api/v1/submissions/bulk`` — apply an operation to multiple submissions.
- ``GET /api/v1/submissions/batch-report.csv?ids=…`` — comparative CSV for the
  provided submission IDs, sorted by latest AI decimal grade (desc).
"""
from __future__ import annotations

import csv
import io
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from kimy.core.deps import SessionDep, require_roles
from kimy.models.user import UserRole
from kimy.schemas.bulk import BulkOutcomeOut, BulkRequest, BulkResponse
from kimy.services import bulk as bulk_service

router = APIRouter(
    prefix="/submissions",
    tags=["bulk"],
    dependencies=[Depends(require_roles(UserRole.coordinator, UserRole.admin))],
)


@router.post("/bulk", response_model=BulkResponse, status_code=status.HTTP_202_ACCEPTED)
async def bulk_apply(
    payload: BulkRequest, session: SessionDep
) -> BulkResponse:
    if payload.operation == "set_status" and payload.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="status is required for set_status",
        )

    if payload.operation == "reprocess_ai":
        outcomes = await bulk_service.reprocess_ai(session, payload.submission_ids)
    elif payload.operation == "set_status":
        assert payload.status is not None  # narrowed by check above
        outcomes = await bulk_service.set_status(
            session, payload.submission_ids, payload.status
        )
    elif payload.operation == "assign_advisor":
        outcomes = await bulk_service.assign_advisor(
            session, payload.submission_ids, payload.advisor_id
        )
    else:  # pragma: no cover — pydantic literal makes this unreachable
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unsupported operation: {payload.operation}",
        )

    succeeded = sum(1 for o in outcomes if o.ok)
    return BulkResponse(
        operation=payload.operation,
        total=len(outcomes),
        succeeded=succeeded,
        failed=len(outcomes) - succeeded,
        outcomes=[
            BulkOutcomeOut(
                submission_id=o.submission_id, ok=o.ok, detail=o.detail
            )
            for o in outcomes
        ],
    )


@router.get("/batch-report.csv")
async def batch_report_csv(
    session: SessionDep,
    ids: Annotated[list[UUID], Query(alias="ids", min_length=1)],
):
    """CSV with one row per submission, sorted by latest AI grade desc."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from kimy.models.ai_evaluation import AIEvaluation
    from kimy.models.submission import Submission
    from kimy.models.submission_version import SubmissionVersion

    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.program),
            selectinload(Submission.versions),
        )
        .where(Submission.id.in_(ids))
    )
    submissions = list((await session.execute(stmt)).scalars().all())

    # Fetch latest AI evaluation per submission in one query.
    latest_version_subq = (
        select(
            SubmissionVersion.submission_id.label("sub_id"),
            SubmissionVersion.id.label("ver_id"),
        )
        .where(SubmissionVersion.submission_id.in_(ids))
        .order_by(
            SubmissionVersion.submission_id,
            SubmissionVersion.version_number.desc(),
        )
        .distinct(SubmissionVersion.submission_id)
        .subquery()
    )
    eval_stmt = (
        select(AIEvaluation, latest_version_subq.c.sub_id)
        .options(selectinload(AIEvaluation.findings))
        .join(latest_version_subq, latest_version_subq.c.ver_id == AIEvaluation.version_id)
    )
    eval_rows = (await session.execute(eval_stmt)).all()
    eval_by_sub: dict[UUID, AIEvaluation] = {
        row.sub_id: row.AIEvaluation for row in eval_rows
    }

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "submission_id",
            "title",
            "chapter",
            "student_name",
            "student_email",
            "program_code",
            "status",
            "ai_grade_20",
            "ai_percentage",
            "structure",
            "content",
            "form",
            "originality",
            "advisor_fit_score",
            "advisor_fit_alert",
            "findings_count",
            "ai_backend",
            "evaluated_at",
        ]
    )

    rows: list[tuple] = []
    for s in submissions:
        ev = eval_by_sub.get(s.id)
        rows.append(
            (
                str(s.id),
                s.title,
                s.chapter or "",
                s.student.full_name if s.student else "",
                s.student.email if s.student else "",
                s.program.code if s.program else "",
                s.status.value,
                f"{ev.decimal_grade:.2f}" if ev else "",
                f"{ev.total_percentage:.2f}" if ev else "",
                f"{ev.structure_score:.2f}" if ev else "",
                f"{ev.content_score:.2f}" if ev else "",
                f"{ev.form_score:.2f}" if ev else "",
                f"{ev.originality_score:.2f}" if ev else "",
                f"{s.advisor_fit_score:.3f}" if s.advisor_fit_score is not None else "",
                "true" if s.advisor_fit_alert else "false",
                len(ev.findings) if ev else 0,
                ev.backend if ev else "",
                ev.created_at.isoformat() if ev else "",
            )
        )
    # Sort by AI grade desc (empty grades last).
    rows.sort(key=lambda r: float(r[7]) if r[7] else -1.0, reverse=True)
    for row in rows:
        writer.writerow(row)

    return Response(
        content=buf.getvalue().encode("utf-8-sig"),  # BOM for Excel
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="kimy_batch_report.csv"'
        },
    )
