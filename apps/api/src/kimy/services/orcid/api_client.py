"""ORCID public-API client.

We use the public v3 API: ``GET /v3.0/{orcid}/works`` (summary) followed by
``GET /v3.0/{orcid}/works/{put-codes}`` (detail) when more than one put-code is
needed. To keep things simple we just list summaries and read enough metadata
from the bulk-works endpoint to fill our model.

Stub mode (when oauth is also stub) returns a fixed list of plausible papers
so the pipeline can be exercised without a real ORCID account.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from kimy.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OrcidWork:
    put_code: str
    title: str
    year: int | None
    journal: str | None
    doi: str | None
    url: str | None


@dataclass(slots=True)
class OrcidPerson:
    given_name: str | None
    family_name: str | None
    affiliation: str | None


def _api_base() -> str:
    settings = get_settings()
    host = "pub.sandbox.orcid.org" if settings.orcid_sandbox else "pub.orcid.org"
    return f"https://{host}/v3.0"


async def fetch_person(orcid_id: str, access_token: str) -> OrcidPerson | None:
    if access_token.startswith("stub."):
        return OrcidPerson(
            given_name="Dev",
            family_name="Advisor",
            affiliation="Universidad de Demostración",
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{_api_base()}/{orcid_id}/person",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
    if not resp.is_success:
        logger.warning("ORCID person fetch failed: %s %s", resp.status_code, resp.text[:200])
        return None
    payload: dict[str, Any] = resp.json()
    name = payload.get("name") or {}
    given = (name.get("given-names") or {}).get("value")
    family = (name.get("family-name") or {}).get("value")
    employments = (
        (payload.get("employments") or {})
        .get("affiliation-group", [])
    )
    affiliation: str | None = None
    if employments:
        first = (employments[0].get("summaries") or [{}])[0]
        org = (first.get("employment-summary") or {}).get("organization") or {}
        affiliation = org.get("name")
    return OrcidPerson(given_name=given, family_name=family, affiliation=affiliation)


async def fetch_works(orcid_id: str, access_token: str) -> list[OrcidWork]:
    if access_token.startswith("stub."):
        return _stub_works()

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{_api_base()}/{orcid_id}/works",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
    if not resp.is_success:
        logger.warning("ORCID works fetch failed: %s %s", resp.status_code, resp.text[:200])
        return []
    payload: dict[str, Any] = resp.json()

    works: list[OrcidWork] = []
    for group in payload.get("group", []):
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        # Use the first (preferred) summary; ORCID groups duplicates.
        summary = summaries[0]
        title_field = (summary.get("title") or {}).get("title") or {}
        title = title_field.get("value") or ""
        if not title:
            continue

        year_field = ((summary.get("publication-date") or {}).get("year") or {})
        year_str = year_field.get("value")
        try:
            year = int(year_str) if year_str else None
        except (TypeError, ValueError):
            year = None

        journal_field = summary.get("journal-title") or {}
        journal = journal_field.get("value")

        external_ids = (summary.get("external-ids") or {}).get("external-id", [])
        doi = None
        for ext in external_ids:
            if (ext.get("external-id-type") or "").lower() == "doi":
                doi = (ext.get("external-id-value") or "").strip() or None
                break

        url = ((summary.get("url") or {}) or {}).get("value")
        put_code = str(summary.get("put-code") or "")
        if not put_code:
            continue

        works.append(
            OrcidWork(
                put_code=put_code,
                title=title[:500],
                year=year,
                journal=journal[:500] if journal else None,
                doi=doi[:200] if doi else None,
                url=url[:500] if url else None,
            )
        )
    return works


def _stub_works() -> list[OrcidWork]:
    """Synthetic publications used in dev / when ORCID isn't configured. Mix of
    NLP, education, and software engineering — enough variety to demonstrate
    the advisor-fit similarity scoring."""
    return [
        OrcidWork(
            put_code="stub-1",
            title="Automated thesis review using large language models",
            year=2024,
            journal="Journal of Educational Technology",
            doi="10.0000/stub.1",
            url=None,
        ),
        OrcidWork(
            put_code="stub-2",
            title="Plagiarism detection with semantic embeddings in academic corpora",
            year=2023,
            journal="Computers & Education",
            doi="10.0000/stub.2",
            url=None,
        ),
        OrcidWork(
            put_code="stub-3",
            title="A retrieval-augmented framework for academic citation validation",
            year=2024,
            journal="Information Processing & Management",
            doi="10.0000/stub.3",
            url=None,
        ),
        OrcidWork(
            put_code="stub-4",
            title="Tutor feedback patterns in postgraduate engineering programs",
            year=2022,
            journal="Higher Education Research & Development",
            doi="10.0000/stub.4",
            url=None,
        ),
    ]
