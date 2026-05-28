"""CSV exporters for coordinator/admin reports.

We render UTF-8 with BOM so Excel opens the files with accents intact, and use
``;`` as separator which Excel-ES expects by default.
"""
from __future__ import annotations

import csv
import io
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.academic_program import AcademicProgram
from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import SubmissionVersion


def _csv_response(headers: list[str], rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(headers)
    writer.writerows(rows)
    # UTF-8 BOM so Excel decodes accents correctly.
    return b"\xef\xbb\xbf" + buf.getvalue().encode("utf-8")


async def submissions_csv(
    session: AsyncSession,
    *,
    program_id: UUID | None = None,
    status: SubmissionStatus | None = None,
) -> bytes:
    """One row per submission, with the latest evaluation joined in."""
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.advisor),
            selectinload(Submission.program),
            selectinload(Submission.versions).selectinload(SubmissionVersion.submission),
        )
        .order_by(Submission.created_at.desc())
    )
    if program_id is not None:
        stmt = stmt.where(Submission.program_id == program_id)
    if status is not None:
        stmt = stmt.where(Submission.status == status)

    submissions = list((await session.execute(stmt)).scalars().all())

    # Fetch latest evaluations per submission in one query.
    version_ids = {
        v.id for s in submissions for v in s.versions
    }
    evals_by_version: dict[UUID, AIEvaluation] = {}
    if version_ids:
        ev_rows = (
            await session.execute(
                select(AIEvaluation).where(AIEvaluation.version_id.in_(version_ids))
            )
        ).scalars().all()
        evals_by_version = {ev.version_id: ev for ev in ev_rows}

    rows: list[list[str]] = []
    for s in submissions:
        latest_v = s.versions[0] if s.versions else None
        evaluation = evals_by_version.get(latest_v.id) if latest_v else None
        rows.append([
            str(s.id),
            s.program.code if s.program else "",
            s.program.name if s.program else "",
            s.title,
            s.chapter or "",
            s.status.value,
            s.student.full_name if s.student else "",
            s.student.email if s.student else "",
            s.advisor.full_name if s.advisor else "",
            s.advisor.email if s.advisor else "",
            f"{evaluation.decimal_grade:.2f}" if evaluation else "",
            f"{evaluation.total_percentage:.1f}" if evaluation else "",
            f"{(s.advisor_fit_score or 0):.2f}" if s.advisor_fit_score is not None else "",
            "sí" if s.advisor_fit_alert else "no",
            str(latest_v.version_number) if latest_v else "0",
            s.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    headers = [
        "ID avance",
        "Código programa",
        "Programa",
        "Título",
        "Capítulo",
        "Estado",
        "Estudiante",
        "Correo estudiante",
        "Asesor",
        "Correo asesor",
        "Nota IA (/20)",
        "% cumplimiento",
        "ORCID fit",
        "Alerta fit",
        "Versión",
        "Creado",
    ]
    return _csv_response(headers, rows)


async def programs_rollup_csv(session: AsyncSession) -> bytes:
    """One row per academic program with aggregated metrics."""
    from kimy.services import stats as stats_service

    overview = await stats_service.overview(session)
    rows: list[list[str]] = []
    for p in overview.grades_per_program:
        rows.append([
            p.program_code,
            p.program_name,
            str(p.submissions_count),
            f"{p.average_grade:.2f}",
        ])

    # Also include programs with zero evaluations (otherwise they're hidden).
    seen = {p.program_code for p in overview.grades_per_program}
    extra_progs = (
        await session.execute(
            select(AcademicProgram).order_by(AcademicProgram.code)
        )
    ).scalars().all()
    for prog in extra_progs:
        if prog.code in seen:
            continue
        count = await session.scalar(
            select(Submission.id).where(Submission.program_id == prog.id).limit(1)
        )
        rows.append([
            prog.code,
            prog.name,
            "0" if count is None else "?",
            "—",
        ])

    return _csv_response(
        ["Código", "Programa", "Avances", "Nota IA promedio (/20)"],
        rows,
    )
