"""Heuristic structure parser.

Builds a tree of sections from an ExtractedDocument:
- If Word headings are present, uses them.
- Else falls back to numbered prefixes like '1.', '1.1', '2.3.4', and roman
  numerals 'I.', 'II.' at the line start.

Phase 4 will refine this with an LLM pass over the same extraction.
"""
from __future__ import annotations

import re
from typing import Any

from kimy.services.documents.extractor import ExtractedDocument, ExtractedParagraph

_NUMBERED_RE = re.compile(
    r"^\s*(?P<num>(?:\d+\.)+\d*|\d+\.)\s+(?P<title>.+?)\s*$"
)
_ROMAN_RE = re.compile(
    r"^\s*(?P<num>(?:I{1,3}|IV|VI{0,3}|IX|X{1,3}|XL|L|XC|C{1,3}))\.\s+(?P<title>[A-ZÁÉÍÓÚÑ][^a-z]{0,80}|[A-ZÁÉÍÓÚÑ].{3,80})\s*$"
)
_ALLCAPS_RE = re.compile(r"^\s*([A-ZÁÉÍÓÚÑ0-9 ÁÉÍÓÚÜ\-:.()]{6,80})\s*$")

# Common Spanish thesis sections — used to map free-form titles to canonical ones.
_CANONICAL_SECTIONS = {
    "resumen": "Resumen",
    "abstract": "Abstract",
    "introduccion": "Introducción",
    "introducción": "Introducción",
    "planteamiento del problema": "Planteamiento del problema",
    "objetivos": "Objetivos",
    "objetivo general": "Objetivos",
    "justificacion": "Justificación",
    "justificación": "Justificación",
    "antecedentes": "Antecedentes",
    "marco teorico": "Marco teórico",
    "marco teórico": "Marco teórico",
    "marco conceptual": "Marco conceptual",
    "hipotesis": "Hipótesis",
    "hipótesis": "Hipótesis",
    "metodologia": "Metodología",
    "metodología": "Metodología",
    "materiales y metodos": "Materiales y métodos",
    "materiales y métodos": "Materiales y métodos",
    "resultados": "Resultados",
    "discusion": "Discusión",
    "discusión": "Discusión",
    "conclusiones": "Conclusiones",
    "recomendaciones": "Recomendaciones",
    "referencias": "Referencias bibliográficas",
    "referencias bibliograficas": "Referencias bibliográficas",
    "referencias bibliográficas": "Referencias bibliográficas",
    "bibliografia": "Referencias bibliográficas",
    "bibliografía": "Referencias bibliográficas",
    "anexos": "Anexos",
    "apendices": "Apéndices",
    "apéndices": "Apéndices",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _canonical(title: str) -> str:
    return _CANONICAL_SECTIONS.get(_normalize(title), title.strip())


def _depth_from_number(num: str) -> int:
    """'1.' → 1, '1.1' → 2, '2.3.4' → 3."""
    cleaned = num.rstrip(".")
    return cleaned.count(".") + 1


def _split_number(text: str) -> tuple[str | None, str]:
    """If text starts with '1.', '2.3', 'I.', return (number, title); else (None, text)."""
    m = _NUMBERED_RE.match(text)
    if m:
        return m.group("num"), m.group("title").strip()
    m = _ROMAN_RE.match(text)
    if m:
        return m.group("num"), m.group("title").strip()
    return None, text.strip()


def _detect_heading(para: ExtractedParagraph) -> tuple[int, str, str | None] | None:
    """Return (level, title, number or None) if paragraph looks like a heading."""
    if para.heading_level is not None and para.heading_level >= 1:
        number, title = _split_number(para.text)
        return (para.heading_level, title, number)

    if m := _NUMBERED_RE.match(para.text):
        num = m.group("num")
        title = m.group("title").strip()
        return (_depth_from_number(num), title, num)

    if m := _ROMAN_RE.match(para.text):
        num = m.group("num")
        title = m.group("title").strip()
        return (1, title, num)

    if (m := _ALLCAPS_RE.match(para.text)) and _normalize(para.text) in _CANONICAL_SECTIONS:
        return (1, para.text.strip().title(), None)

    return None


def parse_structure(doc: ExtractedDocument) -> dict[str, Any]:
    """Convert an extracted document into a structure JSON.

    Output schema:
    {
      "sections": [
        {
          "number": "1." | null,
          "title": "Introducción",
          "canonical_title": "Introducción",
          "level": 1,
          "char_count": 1234,
          "paragraph_count": 8,
          "children": [...]
        }
      ],
      "total_paragraphs": 123,
      "total_chars": 45678,
      "page_count": 0
    }
    """
    sections: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []

    current_chars = 0
    current_paragraphs = 0

    def _flush_running() -> None:
        nonlocal current_chars, current_paragraphs
        if stack:
            stack[-1]["char_count"] += current_chars
            stack[-1]["paragraph_count"] += current_paragraphs
        current_chars = 0
        current_paragraphs = 0

    for para in doc.paragraphs:
        heading = _detect_heading(para)
        if heading is None:
            current_chars += len(para.text)
            current_paragraphs += 1
            continue

        _flush_running()
        level, title, number = heading
        node: dict[str, Any] = {
            "number": number,
            "title": title,
            "canonical_title": _canonical(title),
            "level": level,
            "char_count": 0,
            "paragraph_count": 0,
            "children": [],
        }
        # Pop stack to the parent of this level.
        while stack and stack[-1]["level"] >= level:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            sections.append(node)
        stack.append(node)

    _flush_running()

    total_chars = sum(len(p.text) for p in doc.paragraphs)
    total_paragraphs = len(doc.paragraphs)

    return {
        "sections": sections,
        "total_paragraphs": total_paragraphs,
        "total_chars": total_chars,
        "page_count": doc.page_count,
    }
