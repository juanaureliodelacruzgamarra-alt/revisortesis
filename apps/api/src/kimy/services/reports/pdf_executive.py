"""Executive summary PDF — a single-page dashboard snapshot for coordinators.

Layout:
- Letterhead (shared)
- Title + small caption with the cutoff timestamp
- 2×4 KPI grid (total submissions, avg grade, concordance, ORCID-linked advisors,
  plagiarism alerts, ORCID-fit alerts, low compliance, problematic citations)
- Status distribution table
- Top programs table (avg grade desc)
- "Necesitan atención" table with the flagged submissions
- Disclaimer footer
"""
from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
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
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.submission import Submission
from kimy.models.submission_version import SubmissionVersion
from kimy.services import activity as activity_service
from kimy.services import stats as stats_service
from kimy.services.reports.pdf_letterhead import (
    AURORA_HAIRLINE,
    AURORA_INK,
    AURORA_MUTED,
    AURORA_TEXT,
    AURORA_VIOLET,
    AURORA_VIOLET_SOFT,
    LETTERHEAD_BOTTOM_MARGIN,
    LETTERHEAD_TOP_MARGIN,
    make_letterhead,
)

_STATUS_LABELS = {
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
            spaceAfter=4,
            textColor=AURORA_TEXT,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=4,
            textColor=AURORA_VIOLET,
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            fontSize=9,
            textColor=AURORA_MUTED,
            leading=12,
        ),
        "kpi_label": ParagraphStyle(
            "kpi_label",
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=AURORA_MUTED,
            alignment=TA_LEFT,
        ),
        "kpi_value": ParagraphStyle(
            "kpi_value",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=AURORA_INK,
            alignment=TA_LEFT,
        ),
        "kpi_helper": ParagraphStyle(
            "kpi_helper",
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=AURORA_MUTED,
            alignment=TA_LEFT,
        ),
        "cell": ParagraphStyle(
            "cell",
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
        ),
        "cell_strong": ParagraphStyle(
            "cell_strong",
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            fontName="Helvetica-Bold",
        ),
    }


def _kpi_cell(styles, label: str, value: str, helper: str | None = None) -> Table:
    """A KPI tile rendered as a tiny table so it can sit in the outer grid."""
    rows: list[list[Any]] = [
        [Paragraph(label.upper(), styles["kpi_label"])],
        [Paragraph(value, styles["kpi_value"])],
    ]
    if helper:
        rows.append([Paragraph(helper, styles["kpi_helper"])])
    t = Table(rows, colWidths=[4.0 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
                ("BOX", (0, 0), (-1, -1), 0.5, AURORA_HAIRLINE),
                ("LINEABOVE", (0, 0), (-1, 0), 1.5, AURORA_VIOLET),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _table(rows: list[list[Any]], col_widths: list[float]) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), AURORA_VIOLET),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, AURORA_HAIRLINE),
                ("BOX", (0, 0), (-1, -1), 0.5, AURORA_HAIRLINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _fmt_grade(v: float | None) -> str:
    return f"{v:.2f}" if v is not None else "—"


def _fmt_pct(v: float | None) -> str:
    return f"{v:.1f}%" if v is not None else "—"


async def render_executive_report(session: AsyncSession) -> bytes:
    overview = await stats_service.overview(session)

    # Resolve flagged submissions (fit alert OR AI < 60%) in a focused query.
    flagged_stmt = (
        select(Submission, AIEvaluation)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.advisor),
            selectinload(Submission.program),
        )
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
        .where(
            (Submission.advisor_fit_alert.is_(True))
            | (AIEvaluation.total_percentage < 60),
        )
        .order_by(Submission.created_at.desc())
        .limit(20)
    )
    flagged_rows = (await session.execute(flagged_stmt)).all()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=LETTERHEAD_TOP_MARGIN,
        bottomMargin=LETTERHEAD_BOTTOM_MARGIN,
        title="Reporte ejecutivo · Aurelio",
        author="Aurelio",
    )
    styles = _styles()
    story: list[Any] = []

    story.append(Paragraph("Reporte ejecutivo", styles["h1"]))
    story.append(
        Paragraph(
            "Resumen consolidado de la plataforma Aurelio en este momento.",
            styles["muted"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    # KPI grid 2×4
    kpis = [
        _kpi_cell(styles, "Avances totales", str(overview.total_submissions)),
        _kpi_cell(
            styles,
            "Nota IA promedio",
            _fmt_grade(overview.avg_ai_grade),
            helper=f"/ 20 · {_fmt_pct(overview.avg_ai_percentage)}",
        ),
        _kpi_cell(
            styles,
            "Concordancia IA / Humano",
            _fmt_pct(overview.ai_human_concordance_pct),
            helper="aceptados sin modificar",
        ),
        _kpi_cell(
            styles,
            "Asesores con ORCID",
            str(overview.total_advisors_with_orcid),
        ),
        _kpi_cell(
            styles,
            "Alertas plagio",
            str(overview.plagiarism_alerts),
            helper="≥85% intra-programa",
        ),
        _kpi_cell(
            styles,
            "Alertas ORCID fit",
            str(overview.advisor_fit_alerts),
            helper="afinidad baja",
        ),
        _kpi_cell(
            styles,
            "Bajo cumplimiento",
            str(overview.low_compliance_submissions),
            helper="< 60% en IA",
        ),
        _kpi_cell(
            styles,
            "Citas problemáticas",
            str(overview.citations_problematic),
            helper=f"de {overview.citations_total} extraídas",
        ),
    ]
    # Pack into 2 rows of 4 cells.
    grid_rows = [kpis[0:4], kpis[4:8]]
    grid = Table(
        grid_rows,
        colWidths=[4.3 * cm] * 4,
        rowHeights=[None, None],
    )
    grid.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(grid)
    story.append(Spacer(1, 0.4 * cm))

    # Distribution by status
    story.append(Paragraph("Distribución por estado", styles["h2"]))
    status_rows = [["Estado", "Cantidad"]]
    if overview.submissions_by_status:
        for s in overview.submissions_by_status:
            status_rows.append(
                [_STATUS_LABELS.get(s.status, s.status), str(s.count)]
            )
    else:
        status_rows.append(["—", "0"])
    story.append(_table(status_rows, col_widths=[10.0 * cm, 4.0 * cm]))
    story.append(Spacer(1, 0.4 * cm))

    # Top programs by avg grade
    story.append(Paragraph("Top programas por nota IA promedio", styles["h2"]))
    top_progs = sorted(
        overview.grades_per_program,
        key=lambda p: p.average_grade,
        reverse=True,
    )[:5]
    if not top_progs:
        story.append(
            Paragraph(
                "Aún no hay programas con evaluaciones IA registradas.",
                styles["muted"],
            )
        )
    else:
        prog_rows: list[list[Any]] = [
            ["Código", "Programa", "Avances", "Nota promedio (/20)"],
        ]
        for p in top_progs:
            prog_rows.append([
                Paragraph(p.program_code, styles["cell_strong"]),
                Paragraph(p.program_name, styles["cell"]),
                Paragraph(str(p.submissions_count), styles["cell"]),
                Paragraph(f"{p.average_grade:.2f}", styles["cell"]),
            ])
        story.append(_table(prog_rows, col_widths=[1.8 * cm, 8.5 * cm, 2.5 * cm, 4.0 * cm]))

    story.append(Spacer(1, 0.4 * cm))

    # Flagged submissions
    story.append(Paragraph("Necesitan atención", styles["h2"]))
    if not flagged_rows:
        story.append(
            Paragraph(
                "Ningún avance tiene alertas de plagio, afinidad ORCID baja o "
                "bajo cumplimiento IA en este momento.",
                styles["muted"],
            )
        )
    else:
        rows: list[list[Any]] = [
            ["Programa", "Avance / Estudiante", "Asesor", "Alerta"],
        ]
        seen: set[Any] = set()
        for sub, ev in flagged_rows:
            if sub.id in seen:
                continue
            seen.add(sub.id)
            alerts: list[str] = []
            if sub.advisor_fit_alert:
                alerts.append("ORCID fit bajo")
            if ev is not None and ev.total_percentage < 60:
                alerts.append(f"IA {ev.total_percentage:.0f}%")
            rows.append([
                Paragraph(sub.program.code if sub.program else "—", styles["cell_strong"]),
                Paragraph(
                    f"<b>{sub.title}</b><br/>"
                    f"<font size='7' color='#71717a'>"
                    f"{sub.student.full_name if sub.student else '—'}"
                    f"</font>",
                    styles["cell"],
                ),
                Paragraph(
                    sub.advisor.full_name if sub.advisor else "Sin asignar",
                    styles["cell"],
                ),
                Paragraph(" · ".join(alerts) if alerts else "—", styles["cell"]),
            ])
        story.append(_table(rows, col_widths=[1.8 * cm, 8.5 * cm, 4.0 * cm, 3.5 * cm]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=AURORA_HAIRLINE))
    story.append(
        Paragraph(
            "Documento ejecutivo generado por Aurelio. Cifras calculadas sobre "
            "las últimas evaluaciones IA disponibles. Para detalle por avance, "
            "consultar el reporte de avances completo.",
            styles["muted"],
        )
    )

    letterhead = make_letterhead("Reporte ejecutivo")
    doc.build(story, onFirstPage=letterhead, onLaterPages=letterhead)
    return buf.getvalue()


async def render_activity_report(session: AsyncSession, *, limit: int = 50) -> bytes:
    """Recent activity timeline as a printable PDF."""
    items = await activity_service.recent(session, limit=limit)

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=LETTERHEAD_TOP_MARGIN,
        bottomMargin=LETTERHEAD_BOTTOM_MARGIN,
        title="Reporte de actividad · Aurelio",
        author="Aurelio",
    )
    styles = _styles()
    story: list[Any] = []

    story.append(Paragraph("Reporte de actividad", styles["h1"]))
    story.append(
        Paragraph(
            f"Últimos {len(items)} eventos relevantes (auditoría rápida).",
            styles["muted"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    if not items:
        story.append(Paragraph("Sin actividad registrada.", styles["muted"]))
    else:
        rows: list[list[Any]] = [
            ["Fecha", "Tipo", "Avance", "Descripción"],
        ]
        for it in items:
            rows.append([
                Paragraph(
                    it.occurred_at.strftime("%d/%m/%Y\n%H:%M UTC"),
                    styles["cell"],
                ),
                Paragraph(it.kind.replace("_", " "), styles["cell_strong"]),
                Paragraph(it.submission_title, styles["cell"]),
                Paragraph(
                    f"{it.description}<br/>"
                    f"<font size='7' color='#71717a'>{it.actor_name}</font>",
                    styles["cell"],
                ),
            ])
        story.append(_table(rows, col_widths=[2.4 * cm, 3.0 * cm, 5.5 * cm, 6.1 * cm]))

    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=AURORA_HAIRLINE))
    story.append(
        Paragraph(
            "Eventos sintetizados a partir de las tablas de submissions, "
            "versions y evaluaciones IA. Para auditoría exhaustiva consultar "
            "el panel de Audit del administrador.",
            styles["muted"],
        )
    )

    letterhead = make_letterhead("Reporte de actividad")
    doc.build(story, onFirstPage=letterhead, onLaterPages=letterhead)
    return buf.getvalue()
