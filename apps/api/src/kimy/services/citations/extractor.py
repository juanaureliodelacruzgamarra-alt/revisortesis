"""Reference extractor.

Two strategies, tried in order:
1. LLM (OpenAI gpt-4o-mini in JSON mode) when OPENAI_API_KEY is set — best quality.
2. Regex over the trailing "References" / "Bibliografía" / "Referencias bibliográficas"
   section. Lower recall but works with no API key.

The output schema is always the same: a list of ParsedReference.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field, ValidationError

from kimy.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ParsedReference:
    raw_text: str
    title: str | None
    authors: str | None
    year: int | None
    journal: str | None
    doi: str | None


class _LLMReference(BaseModel):
    raw_text: str = Field(min_length=1)
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    journal: str | None = None
    doi: str | None = None


class _LLMOutput(BaseModel):
    references: list[_LLMReference]


_SECTION_HEADER_RE = re.compile(
    r"(referencias?\s+bibliogr[áa]ficas?|referencias?|bibliograf[íi]a|references?|works\s+cited)",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\((\d{4})[a-z]?\)")
_DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9a-z]+")


def _slice_references_section(full_text: str) -> str:
    """Return text from the first 'References' heading to the end of the doc."""
    match = _SECTION_HEADER_RE.search(full_text)
    if match is None:
        # No explicit section — fall back to the last quarter of the document.
        return full_text[-max(2000, len(full_text) // 4) :]
    return full_text[match.end() :]


def _split_entries(section: str) -> list[str]:
    """Heuristic split of a references section into individual entries.

    Tries blank lines first; if those produce only one big blob, splits on
    leading numbers like "1." or "[1]" or on lines starting with capitalized
    author-like patterns. Filters very short fragments.
    """
    parts = [p.strip() for p in re.split(r"\n\s*\n", section) if p.strip()]
    if len(parts) >= 3:
        return [p for p in parts if len(p) > 30]

    # Try numbered list: "1. Author...\n2. Author..."
    parts = re.split(r"\n\s*(?:\d{1,3}\.|\[\d{1,3}\])\s+", section)
    parts = [p.strip() for p in parts if p.strip()]
    if len(parts) >= 3:
        return [p for p in parts if len(p) > 30]

    # Last resort: split on year-in-parens which APA uses for every ref.
    chunks = re.split(r"(?=\n[A-ZÁÉÍÓÚÑ][^\n]{0,80}\(\d{4}\))", section)
    return [c.strip() for c in chunks if len(c.strip()) > 30]


def _parse_entry_regex(text: str) -> ParsedReference:
    year_match = _YEAR_RE.search(text)
    year = int(year_match.group(1)) if year_match else None

    doi_match = _DOI_RE.search(text)
    doi = doi_match.group(0).rstrip(".,") if doi_match else None

    # APA-ish: "Authors (year). Title. Journal..."
    title: str | None = None
    authors: str | None = None
    journal: str | None = None

    if year_match:
        authors_blob = text[: year_match.start()].strip().rstrip(",").rstrip(".")
        if authors_blob:
            authors = authors_blob[:1000]
        rest = text[year_match.end() :].lstrip(". ").strip()
        # Title is up to the first period followed by space or end.
        title_match = re.match(r"^(.*?)\.", rest)
        if title_match:
            title = title_match.group(1).strip().rstrip(",") or None
            after_title = rest[title_match.end() :].strip()
            # Journal: up to comma/period before volume number, or whole remainder.
            j_match = re.match(r"^([^,0-9]+)", after_title)
            if j_match:
                journal = j_match.group(1).strip(" ,.") or None
        else:
            title = rest[:300] or None

    return ParsedReference(
        raw_text=text[:2000],
        title=title[:500] if title else None,
        authors=authors,
        year=year,
        journal=journal[:500] if journal else None,
        doi=doi,
    )


def _regex_extract(full_text: str) -> list[ParsedReference]:
    section = _slice_references_section(full_text)
    entries = _split_entries(section)
    refs: list[ParsedReference] = []
    for entry in entries:
        if not _YEAR_RE.search(entry) and not _DOI_RE.search(entry):
            continue  # not a citation-looking line
        refs.append(_parse_entry_regex(entry))
    return refs


_LLM_SYSTEM_PROMPT = """Eres un extractor de referencias bibliográficas para tesis académicas.

Tu tarea: leer el texto de la sección de Referencias / Bibliografía y devolver una lista estructurada.

REGLAS:
- Devuelve ÚNICAMENTE un objeto JSON válido (sin Markdown).
- Cada referencia debe incluir: raw_text (el texto original tal cual aparece), title, authors (lista separada por ", " o "; "), year (int), journal, doi (sin el prefijo https://doi.org/).
- Si un campo no aparece en la cita original, ponlo en null. NUNCA inventes datos.
- Ignora títulos de sección, números de página, encabezados.

FORMATO:
{
  "references": [
    {
      "raw_text": "Smith, J. & Doe, A. (2020). The title. Journal, 12(3), 45-67.",
      "title": "The title",
      "authors": "Smith, J.; Doe, A.",
      "year": 2020,
      "journal": "Journal",
      "doi": "10.1234/abc"
    }
  ]
}
"""


def _call_openai(section_text: str, api_key: str) -> list[ParsedReference]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role": "system", "content": _LLM_SYSTEM_PROMPT},
            {"role": "user", "content": f"Sección de referencias:\n\n{section_text[:20000]}"},
        ],
    )
    content = resp.choices[0].message.content or ""
    payload = json.loads(content)
    parsed = _LLMOutput.model_validate(payload)
    return [
        ParsedReference(
            raw_text=r.raw_text,
            title=r.title,
            authors=r.authors,
            year=r.year,
            journal=r.journal,
            doi=r.doi.replace("https://doi.org/", "") if r.doi else None,
        )
        for r in parsed.references
    ]


def extract_references(full_text: str) -> tuple[list[ParsedReference], str]:
    """Return (references, backend_name)."""
    settings = get_settings()
    section = _slice_references_section(full_text)

    if settings.openai_api_key and len(section) > 50:
        try:
            refs = _call_openai(section, settings.openai_api_key)
            if refs:
                return refs, "openai:gpt-4o-mini"
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("openai reference extraction unusable: %s", exc)
        except Exception:
            logger.exception("openai reference extraction failed — using regex")

    return _regex_extract(full_text), "regex"
