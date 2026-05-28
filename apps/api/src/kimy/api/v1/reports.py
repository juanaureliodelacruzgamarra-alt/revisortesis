"""Reports endpoints — JSON for tables, CSV for downloads.

Coordinator + admin only.
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.core.deps import SessionDep, require_roles
from kimy.models.academic_program import AcademicProgram
from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.plagiarism_match import PlagiarismMatch
from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import SubmissionVersion
from kimy.models.user import UserRole
from kimy.schemas.reports import (
    ProgramRollupRow,
    ProgramsRollup,
    SubmissionReportRow,
    SubmissionsReport,
)
from kimy.services.reports import csv_exporter, pdf_executive, pdf_reports

router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(require_roles(UserRole.coordinator, UserRole.admin))],
)


async def _submissions_query(
    session: AsyncSession,
    *,
    program_id: UUID | None,
    status: SubmissionStatus | None,
) -> list[Submission]:
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.advisor),
            selectinload(Submission.program),
            selectinload(Submission.versions),
        )
        .order_by(Submission.created_at.desc())
    )
    if program_id is not None:
        stmt = stmt.where(Submission.program_id == program_id)
    if status is not None:
        stmt = stmt.where(Submission.status == status)
    return list((await session.execute(stmt)).scalars().all())


@router.get("/submissions", response_model=SubmissionsReport)
async def submissions_report(
    session: SessionDep,
    program_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[SubmissionStatus | None, Query()] = None,
) -> SubmissionsReport:
    submissions = await _submissions_query(
        session, program_id=program_id, status=status
    )
    version_ids = {v.id for s in submissions for v in s.versions}
    evals: dict[UUID, AIEvaluation] = {}
    if version_ids:
        ev_rows = (
            await session.execute(
                select(AIEvaluation).where(AIEvaluation.version_id.in_(version_ids))
            )
        ).scalars().all()
        evals = {ev.version_id: ev for ev in ev_rows}

    rows: list[SubmissionReportRow] = []
    for s in submissions:
        latest_v = s.versions[0] if s.versions else None
        ev = evals.get(latest_v.id) if latest_v else None
        rows.append(
            SubmissionReportRow(
                submission_id=str(s.id),
                program_code=s.program.code if s.program else "",
                program_name=s.program.name if s.program else "",
                title=s.title,
                chapter=s.chapter,
                status=s.status.value,
                student_name=s.student.full_name if s.student else "",
                advisor_name=s.advisor.full_name if s.advisor else None,
                decimal_grade=ev.decimal_grade if ev else None,
                total_percentage=ev.total_percentage if ev else None,
                advisor_fit_score=s.advisor_fit_score,
                advisor_fit_alert=s.advisor_fit_alert,
                latest_version=latest_v.version_number if latest_v else 0,
                created_at=s.created_at.isoformat(),
            )
        )
    return SubmissionsReport(
        program_id=str(program_id) if program_id else None,
        status=status.value if status else None,
        rows=rows,
        total=len(rows),
    )


@router.get("/submissions.csv")
async def submissions_csv(
    session: SessionDep,
    program_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[SubmissionStatus | None, Query()] = None,
) -> Response:
    blob = await csv_exporter.submissions_csv(
        session, program_id=program_id, status=status
    )
    return Response(
        content=blob,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="aurelio-avances.csv"',
        },
    )


@router.get("/programs", response_model=ProgramsRollup)
async def programs_rollup(session: SessionDep) -> ProgramsRollup:
    # Submissions per program + avg grade (joined to AIEvaluation via versions).
    grade_stmt = (
        select(
            AcademicProgram.id,
            AcademicProgram.code,
            AcademicProgram.name,
            func.count(func.distinct(Submission.id)).label("subs_count"),
            func.avg(AIEvaluation.decimal_grade).label("avg_grade"),
            func.sum(
                case((Submission.advisor_fit_alert.is_(True), 1), else_=0)
            ).label("fit_alerts"),
        )
        .join(Submission, Submission.program_id == AcademicProgram.id, isouter=True)
        .join(
            SubmissionVersion,
            SubmissionVersion.submission_id == Submission.id,
            isouter=True,
        )
        .join(
            AIEvaluation,
            AIEvaluation.version_id == SubmissionVersion.id,
            isouter=True,
        )
        .group_by(AcademicProgram.id, AcademicProgram.code, AcademicProgram.name)
        .order_by(AcademicProgram.code)
    )
    grade_rows = (await session.execute(grade_stmt)).all()

    # Plagiarism alerts per program: distinct submissions with at least one match.
    plag_stmt = (
        select(
            AcademicProgram.id,
            func.count(func.distinct(Submission.id)),
        )
        .join(Submission, Submission.program_id == AcademicProgram.id)
        .join(SubmissionVersion, SubmissionVersion.submission_id == Submission.id)
        .join(PlagiarismMatch, PlagiarismMatch.version_id == SubmissionVersion.id)
        .group_by(AcademicProgram.id)
    )
    plag_map: dict[UUID, int] = {
        pid: int(c) for pid, c in (await session.execute(plag_stmt)).all()
    }

    rows = [
        ProgramRollupRow(
            program_id=str(pid),
            program_code=code,
            program_name=name,
            submissions_count=int(subs_count or 0),
            average_grade=float(avg_grade) if avg_grade is not None else None,
            plagiarism_alerts=plag_map.get(pid, 0),
            fit_alerts=int(fit_alerts or 0),
        )
        for pid, code, name, subs_count, avg_grade, fit_alerts in grade_rows
    ]
    return ProgramsRollup(rows=rows)


@router.get("/programs.csv")
async def programs_csv(session: SessionDep) -> Response:
    blob = await csv_exporter.programs_rollup_csv(session)
    return Response(
        content=blob,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="aurelio-programas.csv"',
        },
    )


@router.get("/submissions.pdf")
async def submissions_pdf(
    session: SessionDep,
    program_id: Annotated[UUID | None, Query()] = None,
    status: Annotated[SubmissionStatus | None, Query()] = None,
) -> Response:
    blob = await pdf_reports.render_submissions_report(
        session, program_id=program_id, status=status
    )
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="aurelio-avances.pdf"',
        },
    )


@router.get("/programs.pdf")
async def programs_pdf(session: SessionDep) -> Response:
    blob = await pdf_reports.render_programs_report(session)
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="aurelio-programas.pdf"',
        },
    )


@router.get("/executive.pdf")
async def executive_pdf(session: SessionDep) -> Response:
    """One-page executive snapshot: KPIs + distribution + top programs + flagged."""
    blob = await pdf_executive.render_executive_report(session)
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="aurelio-ejecutivo.pdf"',
        },
    )


@router.get("/activity.pdf")
async def activity_pdf(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Response:
    """Printable timeline of recent events for quick audit."""
    blob = await pdf_executive.render_activity_report(session, limit=limit)
    return Response(
        content=blob,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="aurelio-actividad.pdf"',
        },
    )
