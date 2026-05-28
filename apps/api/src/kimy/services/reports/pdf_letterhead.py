"""Shared Aurelio letterhead used by every PDF report.

Renders on every page via the `onFirstPage` / `onLaterPages` callbacks of
``SimpleDocTemplate``. Includes:
- Top violet accent band
- Logo badge ("A" on violet square) + "Aurelio" wordmark + tagline
- Right column with institutional info (UNT · Escuela de Posgrado) and
  generation timestamp
- Bottom footer with the report kind + page number

Use ``LETTERHEAD_TOP_MARGIN`` / ``LETTERHEAD_BOTTOM_MARGIN`` when configuring
``SimpleDocTemplate`` so the body content doesn't collide with the membrete.
"""
from __future__ import annotations

from datetime import UTC, datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas

# Aurora brand colors (mirror frontend tokens in apps/web/src/app/globals.css).
AURORA_VIOLET = colors.HexColor("#7c3aed")
AURORA_VIOLET_SOFT = colors.HexColor("#a78bfa")
AURORA_INK = colors.HexColor("#0b0e2a")
AURORA_TEXT = colors.HexColor("#1f2937")
AURORA_MUTED = colors.HexColor("#71717a")
AURORA_HAIRLINE = colors.HexColor("#d4d4d8")

# Space the body must leave for the letterhead at the top of every page,
# and for the footer at the bottom. Use these as ``topMargin`` /
# ``bottomMargin`` of SimpleDocTemplate.
LETTERHEAD_TOP_MARGIN = 3.0 * cm
LETTERHEAD_BOTTOM_MARGIN = 1.8 * cm


def make_letterhead(report_kind: str):
    """Return a ``(canvas, doc) -> None`` callback for SimpleDocTemplate.

    ``report_kind`` is rendered in the footer left ("Aurelio · {report_kind}").
    """

    def draw(canvas: Canvas, doc) -> None:
        canvas.saveState()
        width, height = A4

        # 1) Top violet accent band.
        canvas.setFillColor(AURORA_VIOLET)
        canvas.rect(0, height - 0.18 * cm, width, 0.18 * cm, fill=1, stroke=0)

        # 2) Logo badge (rounded square with "A").
        badge_x = 2.0 * cm
        badge_y = height - 2.15 * cm
        badge_size = 0.95 * cm
        canvas.setFillColor(AURORA_VIOLET)
        canvas.roundRect(
            badge_x, badge_y, badge_size, badge_size, 0.18 * cm, fill=1, stroke=0
        )
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawCentredString(
            badge_x + badge_size / 2,
            badge_y + badge_size / 2 - 0.18 * cm,
            "A",
        )

        # 3) Wordmark + tagline.
        text_x = badge_x + badge_size + 0.35 * cm
        canvas.setFillColor(AURORA_INK)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawString(text_x, height - 1.6 * cm, "Aurelio")
        canvas.setFillColor(AURORA_MUTED)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(
            text_x, height - 2.0 * cm, "REVISIÓN ACADÉMICA CON IA"
        )

        # 4) Right column — institutional info + generation timestamp.
        canvas.setFillColor(AURORA_TEXT)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawRightString(
            width - 2.0 * cm, height - 1.45 * cm,
            "Universidad Nacional de Trujillo",
        )
        canvas.setFillColor(AURORA_MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            width - 2.0 * cm, height - 1.8 * cm, "Escuela de Posgrado"
        )
        canvas.drawRightString(
            width - 2.0 * cm, height - 2.15 * cm,
            datetime.now(UTC).strftime("Generado %d/%m/%Y · %H:%M UTC"),
        )

        # 5) Bottom: hairline + footer text.
        canvas.setStrokeColor(AURORA_HAIRLINE)
        canvas.setLineWidth(0.4)
        canvas.line(2.0 * cm, 1.35 * cm, width - 2.0 * cm, 1.35 * cm)
        canvas.setFillColor(AURORA_MUTED)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            2.0 * cm, 0.95 * cm, f"Aurelio · {report_kind}"
        )
        canvas.drawRightString(
            width - 2.0 * cm, 0.95 * cm, f"Página {doc.page}"
        )

        canvas.restoreState()

    return draw
