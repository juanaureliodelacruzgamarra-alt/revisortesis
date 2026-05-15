"""Citation validator orchestrator.

For each ParsedReference:
1. If a DOI was extracted, try to look it up directly.
2. Otherwise, search by title.
3. Compare CrossRef's normalized title and year against the student's claim.
4. Assign a status:
   - verified: title similarity >= 0.85 AND year matches (±1) AND DOI matches if given.
   - partial: title similarity >= 0.55 (probable typo / minor formatting drift).
   - not_found: nothing came back from CrossRef.
   - hallucinated: not_found AND the cite has no DOI AND the title smells fake.

The "hallucinated" heuristic is intentionally conservative — false positives here
hurt the student more than missing a real hallucination.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from difflib import SequenceMatcher
from typing import Any
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.models.citation import Citation, CitationStatus
from kimy.services.citations.crossref import CrossRefClient
from kimy.services.citations.extractor import ParsedReference, extract_references

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CitationResult:
    raw_text: str
    title: str | None
    authors: str | None
    year: int | None
    journal: str | None
    doi: str | None
    status: CitationStatus
    crossref_metadata: dict[str, Any] | None
    message: str | None


_WORD_RE = re.compile(r"[a-z0-9]+")


def _normalize_title(title: str | None) -> str:
    if not title:
        return ""
    tokens = _WORD_RE.findall(title.lower())
    return " ".join(tokens)


def _title_similarity(a: str | None, b: str | None) -> float:
    na, nb = _normalize_title(a), _normalize_title(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def _looks_fake(ref: ParsedReference) -> bool:
    """Heuristic for the 'hallucinated' label. Used only when CrossRef has nothing.

    Signals (any TWO):
    - Title is implausibly generic ('estudio sobre x', 'analisis de y') with no
      domain-specific noun.
    - No DOI AND no journal AND no year.
    - Authors string has > 6 identical surnames.
    """
    signals = 0
    if not ref.doi and not ref.journal and not ref.year:
        signals += 1
    if ref.title:
        words = _WORD_RE.findall(ref.title.lower())
        # Very short titles with only stop-like words.
        generic = {"estudio", "analisis", "investigacion", "tesis", "trabajo", "research", "study"}
        if len(words) <= 5 and any(w in generic for w in words):
            signals += 1
    if ref.authors:
        surnames = re.findall(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}", ref.authors)
        if len(set(surnames)) <= 1 and len(surnames) > 2:
            signals += 1
    return signals >= 2


def _classify(ref: ParsedReference, hit: dict[str, Any] | None) -> tuple[CitationStatus, str | None]:
    if hit is None:
        if _looks_fake(ref):
            return CitationStatus.hallucinated, (
                "No se encontró en CrossRef y la referencia presenta patrones inusuales "
                "(faltan DOI, año o revista; título genérico)."
            )
        return CitationStatus.not_found, "No se encontró en CrossRef."

    # CrossRef titles are arrays.
    crossref_title = (hit.get("title") or [None])[0]
    crossref_year = (
        hit.get("issued", {})
        .get("date-parts", [[None]])[0][0]
    )
    crossref_doi = (hit.get("DOI") or "").lower()

    similarity = _title_similarity(ref.title, crossref_title)
    year_ok = ref.year is None or crossref_year is None or abs(ref.year - int(crossref_year)) <= 1
    doi_match = ref.doi is None or (ref.doi.lower().strip() == crossref_doi)

    if similarity >= 0.85 and year_ok and doi_match:
        return CitationStatus.verified, None

    notes: list[str] = []
    if similarity < 0.85:
        notes.append(
            f'el título publicado en CrossRef es "{crossref_title}" (similitud {similarity:.2f})'
        )
    if not year_ok:
        notes.append(f"el año publicado es {crossref_year}")
    if not doi_match:
        notes.append(f"el DOI registrado es {crossref_doi}")
    msg = "Coincidencia parcial: " + "; ".join(notes) if notes else None

    if similarity >= 0.55:
        return CitationStatus.partial, msg
    return CitationStatus.not_found, msg or "Coincidencia muy débil con CrossRef."


async def _lookup_one(client: CrossRefClient, ref: ParsedReference) -> dict[str, Any] | None:
    if ref.doi:
        hit = await client.lookup_doi(ref.doi)
        if hit:
            return hit
    if ref.title and len(ref.title) >= 8:
        return await client.search_by_title(ref.title)
    return None


async def validate_version(
    session: AsyncSession,
    *,
    version_id: UUID,
    full_text: str,
) -> tuple[list[CitationResult], str]:
    """Extract references from full_text, validate against CrossRef, persist.

    Returns (results, extractor_backend).
    """
    refs, extractor_backend = extract_references(full_text)

    # Idempotent: wipe prior citations for this version.
    await session.execute(delete(Citation).where(Citation.version_id == version_id))
    await session.flush()

    if not refs:
        await session.commit()
        return [], extractor_backend

    results: list[CitationResult] = []
    async with CrossRefClient() as client:
        for ref in refs:
            try:
                hit = await _lookup_one(client, ref)
            except Exception:  # noqa: BLE001
                logger.exception("CrossRef lookup crashed for ref: %s", ref.title)
                hit = None

            status, message = _classify(ref, hit)
            results.append(
                CitationResult(
                    raw_text=ref.raw_text,
                    title=ref.title,
                    authors=ref.authors,
                    year=ref.year,
                    journal=ref.journal,
                    doi=ref.doi,
                    status=status,
                    crossref_metadata=hit,
                    message=message,
                )
            )

    for r in results:
        session.add(
            Citation(
                version_id=version_id,
                raw_text=r.raw_text,
                title=r.title,
                authors=r.authors,
                year=r.year,
                journal=r.journal,
                doi=r.doi,
                crossref_status=r.status,
                crossref_metadata=r.crossref_metadata,
                crossref_message=r.message,
                checked_at=datetime.now(UTC),
            )
        )
    await session.commit()
    return results, extractor_backend
