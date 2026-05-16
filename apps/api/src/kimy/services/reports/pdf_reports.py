"""Coordinator PDF reports — submissions list and program rollup.

Both use the shared Aurelio letterhead (``pdf_letterhead.make_letterhead``).
"""
from __future__ import annotations

from io import BytesIO
from typing import Any
from uuid import UUID

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.academic_program import AcademicProgram
from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.plagiarism_match import PlagiarismMatch
from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import SubmissionVersion
from kimy.services.reports.pdf_letterhead import (
    AURORA_HAIRLINE,
    AURORA_MUTED,
    AURORA_TEXT,
    AURORA_VIOLET,
    LETTERHEAD_BOTTOM_MARGIN,
    LETTERHEAD_TOP_MARGIN,
    make_letterhead,
)

_STATUS_LABELS: dict[str, str] = {
    "draft": "Borrador",
    "in_progress": "En proceso",
    "observed": "Observado",
    "approved": "Aprobado",
    "rejected": "Rechazado",
}


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=18,
            leading=22,
            spaceBefore=0,
            spaceAfter=4,
            textColor=AURORA_TEXT,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=8,
            spaceAfter=4,
            textColor=AURORA_TEXT,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            fontSize=9,
            textColor=AURORA_MUTED,
            leading=12,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
        ),
        "cell": ParagraphStyle(
            "cell",
            parent=base["BodyText"],
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
        ),
        "cell_strong": ParagraphStyle(
            "cell_strong",
            parent=base["BodyText"],
            fontSize=8.5,
            leading=11,
            alignment=TA_LEFT,
            textColor=AURORA_TEXT,
            fontName="Helvetica-Bold",
        ),
    }


def _styled_table(
    rows: list[list[Any]],
    col_widths: list[float],
    *,
    align_right_cols: tuple[int, ...] = (),
) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), AURORA_VIOLET),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [colors.white, colors.HexColor("#fafafa")],
        ),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, AURORA_HAIRLINE),
        ("BOX", (0, 0), (-1, -1), 0.5, AURORA_HAIRLINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for col in align_right_cols:
        style.append(("ALIGN", (col, 1), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


# ---------------------------------------------------------------------------
# Submissions report
# ---------------------------------------------------------------------------


async def render_submissions_report(
    session: AsyncSession,
    *,
    program_id: UUID | None = None,
    status: SubmissionStatus | None = None,
) -> bytes:
    """List of submissions, optionally filtered, with their latest AI grade."""
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
    submissions = list((await session.execute(stmt)).scalars().all())

    version_ids = {v.id for s in submissions for v in s.versions}
    evals: dict[UUID, AIEvaluation] = {}
    if version_ids:
        ev_rows = (
            await session.execute(
                select(AIEvaluation).where(AIEvaluation.version_id.in_(version_ids))
            )
        ).scalars().all()
        evals = {ev.version_id: ev for ev in ev_rows}

    # Program filter context for the header summary.
    program_label = None
    if program_id is not None:
        prog = await session.get(AcademicProgram, program_id)
        if prog is not None:
            program_label = f"[{prog.code}] {prog.name}"

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=LETTERHEAD_TOP_MARGIN,
        bottomMargin=LETTERHEAD_BOTTOM_MARGIN,
        title="Reporte de avances · Aurelio",
        author="Aurelio",
    )
    styles = _styles()
    story: list[Any] = []

    story.append(Paragraph("Reporte de avances", styles["h1"]))
    filters: list[str] = []
    if program_label:
        filters.append(f"Programa: {program_label}")
    if status is not None:
        filters.append(f"Estado: {_STATUS_LABELS.get(status.value, status.value)}")
    filters.append(f"Total: {len(submissions)} avance(s)")
    story.append(Paragraph(" · ".join(filters), styles["muted"]))
    story.append(Spacer(1, 0.4 * cm))

    if not submissions:
        story.append(
            Paragraph(
                "No hay avances que coincidan con los filtros indicados.",
                styles["body"],
            )
        )
    else:
        styles_cell = styles["cell"]
        styles_strong = styles["cell_strong"]
        rows: list[list[Any]] = [
            [
                "Programa",
                "Título",
                "Estudiante",
                "Asesor",
                "Estado",
                "Nota IA",
                "Cumpl.",
                "Alertas",
            ]
        ]
        for s in submissions:
            latest_v = s.versions[0] if s.versions else None
            ev = evals.get(latest_v.id) if latest_v else None

            alerts: list[str] = []
            if s.advisor_fit_alert:
                alerts.append("ORCID")
            if ev and ev.total_percentage < 60:
                alerts.append(f"IA {ev.total_percentage:.0f}%")

            rows.append([
                Paragraph(s.program.code if s.program else "—", styles_strong),
                Paragraph(s.title, styles_cell),
                Paragraph(s.student.full_name if s.student else "—", styles_cell),
                Paragraph(s.advisor.full_name if s.advisor else "—", styles_cell),
                Paragraph(
                    _STATUS_LABELS.get(s.status.value, s.status.value),
                    styles_cell,
                ),
                Paragraph(
                    f"{ev.decimal_grade:.2f}" if ev else "—",
                    styles_cell,
                ),
                Paragraph(
                    f"{ev.total_percentage:.0f}%" if ev else "—",
                    styles_cell,
                ),
                Paragraph(", ".join(alerts) if alerts else "—", styles_cell),
            ])

        # 27 cm of usable width (A4 landscape minus margins).
        story.append(
            _styled_table(
                rows,
                col_widths=[
                    1.8 * cm,  # Programa
                    7.0 * cm,  # Título
                    4.5 * cm,  # Estudiante
                    4.5 * cm,  # Asesor
                    2.5 * cm,  # Estado
                    1.6 * cm,  # Nota IA
                    1.6 * cm,  # Cumplimiento
                    2.5 * cm,  # Alertas
                ],
                align_right_cols=(5, 6),
            )
        )

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=AURORA_HAIRLINE))
    story.append(
        Paragraph(
            "Documento generado automáticamente por la plataforma Aurelio. "
            "Las decisiones académicas finales son responsabilidad del coordinador.",
            styles["muted"],
        )
    )

    letterhead = make_letterhead("Reporte de avances")
    doc.build(story, onFirstPage=letterhead, onLaterPages=letterhead)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Programs rollup report
# ---------------------------------------------------------------------------


async def render_programs_report(session: AsyncSession) -> bytes:
    """Per-program rollup: submissions, avg AI grade, alerts."""
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

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=LETTERHEAD_TOP_MARGIN,
        bottomMargin=LETTERHEAD_BOTTOM_MARGIN,
        title="Reporte por programa · Aurelio",
        author="Aurelio",
    )
    styles = _styles()
    story: list[Any] = []

    story.append(Paragraph("Reporte por programa", styles["h1"]))
    total_subs = sum(int(r[3] or 0) for r in grade_rows)
    story.append(
        Paragraph(
            f"{len(grade_rows)} programa(s) · {total_subs} avance(s) totales",
            styles["muted"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    if not grade_rows:
        story.append(
            Paragraph(
                "Aún no hay programas registrados en la plataforma.",
                styles["body"],
            )
        )
    else:
        styles_cell = styles["cell"]
        styles_strong = styles["cell_strong"]
        rows: list[list[Any]] = [
            [
                "Código",
                "Programa",
                "Avances",
                "Nota IA promedio",
                "Alertas plagio",
                "Alertas ORCID fit",
            ]
        ]
        for pid, code, name, subs_count, avg_grade, fit_alerts in grade_rows:
            rows.append([
                Paragraph(code, styles_strong),
                Paragraph(name, styles_cell),
                Paragraph(str(int(subs_count or 0)), styles_cell),
                Paragraph(
                    f"{float(avg_grade):.2f} / 20" if avg_grade is not None else "—",
                    styles_cell,
                ),
                Paragraph(str(plag_map.get(pid, 0)), styles_cell),
                Paragraph(str(int(fit_alerts or 0)), styles_cell),
            ])
        story.append(
            _styled_table(
                rows,
                col_widths=[
                    1.6 * cm,  # Código
                    7.5 * cm,  # Programa
                    1.8 * cm,  # Avances
                    3.2 * cm,  # Nota IA
                    1.8 * cm,  # Alertas plagio
                    1.8 * cm,  # Alertas fit
                ],
                align_right_cols=(2, 3, 4, 5),
            )
        )

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=AURORA_HAIRLINE))
    story.append(
        Paragraph(
            "Documento generado automáticamente por la plataforma Aurelio. "
            "Promedios calculados sobre las últimas evaluaciones IA disponibles "
            "por avance.",
            styles["muted"],
        )
    )

    letterhead = make_letterhead("Reporte por programa")
    doc.build(story, onFirstPage=letterhead, onLaterPages=letterhead)
    return buf.getvalue()
