"""Acta de revisión — single-submission PDF report.

Generated on-demand via reportlab so we don't need a system-level PDF engine
(weasyprint/wkhtmltopdf) on Windows. The output includes:
- Header with KIMY branding + submission metadata + student/advisor
- AI evaluation summary (executive + scores per dimension)
- Findings grouped by severity, with the advisor's human action when present
- Plagiarism matches summary
- Citation validation rollup
- Footer with the date the acta was generated
"""
from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
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

from kimy.models.ai_evaluation import AIEvaluation
from kimy.models.ai_finding import FindingSeverity
from kimy.models.citation import CitationStatus
from kimy.models.submission import Submission, SubmissionStatus

_SEVERITY_LABELS = {
    FindingSeverity.critical: ("Crítico", colors.HexColor("#b91c1c")),
    FindingSeverity.major: ("Mayor", colors.HexColor("#b45309")),
    FindingSeverity.minor: ("Menor", colors.HexColor("#52525b")),
    FindingSeverity.suggestion: ("Sugerencia", colors.HexColor("#3f3f46")),
}
_STATUS_LABELS: dict[SubmissionStatus, str] = {
    SubmissionStatus.draft: "Borrador",
    SubmissionStatus.in_progress: "En proceso",
    SubmissionStatus.observed: "Observado",
    SubmissionStatus.approved: "Aprobado",
    SubmissionStatus.rejected: "Rechazado",
}
_HUMAN_ACTION_LABELS = {
    "accepted": "Aceptado por el asesor",
    "modified": "Modificado por el asesor",
    "rejected": "Descartado por el asesor",
}
_CITATION_LABELS = {
    CitationStatus.verified: "Verificada",
    CitationStatus.partial: "Parcial",
    CitationStatus.not_found: "No encontrada",
    CitationStatus.hallucinated: "Posible invento",
    CitationStatus.pending: "Pendiente",
}


def _styles():
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontSize=20,
            leading=24,
            spaceBefore=0,
            spaceAfter=4,
            textColor=colors.HexColor("#0f172a"),
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontSize=13,
            leading=16,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#1f2937"),
        ),
        "muted": ParagraphStyle(
            "muted",
            parent=base["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#71717a"),
            leading=12,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            alignment=TA_LEFT,
        ),
        "finding_title": ParagraphStyle(
            "finding_title",
            parent=base["BodyText"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#111827"),
            spaceAfter=2,
        ),
        "finding_section": ParagraphStyle(
            "finding_section",
            parent=base["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#52525b"),
            leading=11,
        ),
    }


def _table_with_header(rows: list[list[Any]], col_widths: list[float]) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f4f5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e4e4e7")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d4d4d8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def render_acta(
    *,
    submission: Submission,
    evaluation: AIEvaluation | None,
    advisor_name: str | None,
    advisor_orcid: str | None,
    plagiarism_groups: list[dict[str, Any]],  # [{matched_student, matched_title, best, count}]
    citations_summary: dict[str, int],
    advisor_fit_score: float | None,
) -> bytes:
    """Return the acta as PDF bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title=f"Acta KIMY - {submission.title}",
        author="KIMY",
    )
    styles = _styles()
    story: list[Any] = []

    # Header
    story.append(Paragraph("KIMY · Acta de revisión", styles["h1"]))
    story.append(
        Paragraph(
            f"Generada el {datetime.now(UTC).strftime('%d/%m/%Y %H:%M UTC')}",
            styles["muted"],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    # Metadata
    student_email = submission.student.email if submission.student else "—"
    student_name = submission.student.full_name if submission.student else "—"
    meta_rows = [
        ["Avance", submission.title],
        ["Capítulo", submission.chapter or "—"],
        ["Programa", f"[{submission.program.code}] {submission.program.name}" if submission.program else "—"],
        ["Estado", _STATUS_LABELS.get(submission.status, submission.status.value)],
        ["Estudiante", f"{student_name} ({student_email})"],
        ["Asesor",
            (f"{advisor_name} — ORCID {advisor_orcid}" if advisor_orcid else (advisor_name or "Sin asignar"))],
        ["Afinidad asesor↔tesis",
            (f"{advisor_fit_score * 100:.1f}%" if advisor_fit_score is not None else "n/d")],
    ]
    story.append(_table_with_header([["Campo", "Valor"], *meta_rows], col_widths=[4.5 * cm, 11.0 * cm]))

    # Evaluation summary
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("1. Evaluación automatizada (IA)", styles["h2"]))
    if evaluation is None:
        story.append(Paragraph("Aún no se ha producido una evaluación de IA para este avance.", styles["body"]))
    else:
        story.append(
            Paragraph(
                f"Backend: <b>{evaluation.backend}</b> · Modelo: {evaluation.model} · "
                f"Prompt: {evaluation.prompt_version} · Procesado en {evaluation.duration_ms} ms",
                styles["muted"],
            )
        )
        story.append(Spacer(1, 0.15 * cm))
        story.append(Paragraph(evaluation.executive_summary or "—", styles["body"]))
        story.append(Spacer(1, 0.25 * cm))

        score_rows = [
            ["Dimensión", "Puntaje (0-100)", "Peso"],
            ["Estructura", f"{evaluation.structure_score:.1f}", "30%"],
            ["Contenido", f"{evaluation.content_score:.1f}", "40%"],
            ["Forma", f"{evaluation.form_score:.1f}", "20%"],
            ["Originalidad", f"{evaluation.originality_score:.1f}", "10%"],
            ["Cumplimiento total", f"{evaluation.total_percentage:.1f}%", "—"],
            ["Nota decimal", f"{evaluation.decimal_grade:.2f} / 20", "—"],
        ]
        story.append(_table_with_header(score_rows, col_widths=[5.0 * cm, 5.0 * cm, 5.5 * cm]))

    # Findings
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("2. Hallazgos", styles["h2"]))
    findings = list(evaluation.findings) if evaluation else []
    if not findings:
        story.append(Paragraph("Sin hallazgos registrados.", styles["body"]))
    else:
        # Group by effective severity (human override beats AI).
        groups: dict[FindingSeverity, list[Any]] = {s: [] for s in FindingSeverity}
        for f in findings:
            sev = f.human_severity_override or f.severity
            groups[sev].append(f)

        for sev in (
            FindingSeverity.critical,
            FindingSeverity.major,
            FindingSeverity.minor,
            FindingSeverity.suggestion,
        ):
            items = groups.get(sev, [])
            if not items:
                continue
            label, color = _SEVERITY_LABELS[sev]
            story.append(Spacer(1, 0.15 * cm))
            sev_style = ParagraphStyle(
                f"sev_{sev.value}",
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                textColor=color,
                spaceAfter=4,
            )
            story.append(Paragraph(f"{label} — {len(items)} hallazgo(s)", sev_style))
            for f in items:
                title_bits = []
                if f.section:
                    title_bits.append(f.section)
                title_bits.append(f.type.value)
                story.append(
                    Paragraph(
                        f"<b>{f.description}</b>",
                        styles["finding_title"],
                    )
                )
                story.append(
                    Paragraph(
                        " · ".join(title_bits),
                        styles["finding_section"],
                    )
                )
                if f.instruction:
                    story.append(
                        Paragraph(f"<i>Corrección:</i> {f.instruction}", styles["body"])
                    )
                if f.example:
                    story.append(
                        Paragraph(f"<i>Ejemplo:</i> {f.example}", styles["body"])
                    )
                if f.recommendation:
                    story.append(
                        Paragraph(
                            f"<i>Recomendación:</i> {f.recommendation}", styles["body"]
                        )
                    )
                if f.human_action:
                    note = _HUMAN_ACTION_LABELS.get(f.human_action.value, f.human_action.value)
                    if f.human_comment:
                        note += f" — “{f.human_comment}”"
                    story.append(Paragraph(note, styles["muted"]))
                story.append(Spacer(1, 0.15 * cm))

    # Plagiarism
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("3. Detección de plagio (intra-programa)", styles["h2"]))
    if not plagiarism_groups:
        story.append(Paragraph("No se detectaron similitudes significativas (≥85%) con avances previos del programa.", styles["body"]))
    else:
        rows = [["Avance similar", "Estudiante", "Similitud máx.", "Fragmentos"]]
        for g in plagiarism_groups:
            rows.append(
                [
                    g["matched_title"][:60],
                    g["matched_student"][:40],
                    f"{g['best_similarity'] * 100:.1f}%",
                    str(g["chunk_count"]),
                ]
            )
        story.append(_table_with_header(rows, col_widths=[6.5 * cm, 5.5 * cm, 2.5 * cm, 2.0 * cm]))

    # Citations
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("4. Validación de citas (CrossRef)", styles["h2"]))
    total_cits = sum(citations_summary.values())
    if total_cits == 0:
        story.append(Paragraph("No se detectaron citas bibliográficas para validar.", styles["body"]))
    else:
        rows = [["Estado", "Cantidad"]]
        for s in CitationStatus:
            n = citations_summary.get(s.value, 0)
            if n == 0:
                continue
            rows.append([_CITATION_LABELS.get(s, s.value), str(n)])
        story.append(_table_with_header(rows, col_widths=[10.5 * cm, 5.0 * cm]))
        story.append(Paragraph(f"Total de citas: {total_cits}", styles["muted"]))

    # Footer
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#d4d4d8")))
    story.append(
        Paragraph(
            "Este documento fue generado automáticamente por la plataforma KIMY. "
            "Las decisiones académicas finales son responsabilidad del asesor y del coordinador del programa.",
            styles["muted"],
        )
    )

    doc.build(story)
    return buf.getvalue()
