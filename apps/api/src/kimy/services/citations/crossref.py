"""CrossRef API client.

Polite-pool compliance:
- Identifies via User-Agent with mailto (configured in settings.crossref_user_agent).
- Self-imposed 1 req/s rate limit (well below CrossRef's published 50 req/s).
- Handles 429 / 5xx with a single backoff retry.

Two operations:
- ``lookup_doi(doi)`` -> CrossRef work record or None.
- ``search_by_title(title)`` -> top hit or None.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from urllib.parse import quote

import httpx

from kimy.core.config import get_settings

logger = logging.getLogger(__name__)

CROSSREF_BASE = "https://api.crossref.org"
MIN_INTERVAL_SECONDS = 1.0


class CrossRefClient:
    """Async client with a per-instance rate limit. One instance per pipeline run."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = httpx.AsyncClient(
            base_url=CROSSREF_BASE,
            timeout=httpx.Timeout(15.0),
            headers={
                "User-Agent": settings.crossref_user_agent,
                "Accept": "application/json",
            },
        )
        self._lock = asyncio.Lock()
        self._last_call_at: float = 0.0

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> CrossRefClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.aclose()

    async def _throttle(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = MIN_INTERVAL_SECONDS - (now - self._last_call_at)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call_at = time.monotonic()

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict[str, Any] | None:
        for attempt in range(2):
            await self._throttle()
            try:
                response = await self._client.get(path, params=params or {})
            except httpx.HTTPError as exc:
                logger.warning("CrossRef HTTP error on %s: %s", path, exc)
                if attempt == 0:
                    await asyncio.sleep(2.0)
                    continue
                return None
            if response.status_code == 404:
                return None
            if response.status_code >= 500 or response.status_code == 429:
                logger.warning(
                    "CrossRef %s on %s — retrying", response.status_code, path
                )
                if attempt == 0:
                    await asyncio.sleep(2.0)
                    continue
                return None
            if not response.is_success:
                logger.warning("CrossRef unexpected status %s on %s", response.status_code, path)
                return None
            try:
                payload = response.json()
            except ValueError:
                logger.warning("CrossRef non-JSON response on %s", path)
                return None
            return payload.get("message")
        return None

    async def lookup_doi(self, doi: str) -> dict[str, Any] | None:
        clean = doi.strip().rstrip(".,").removeprefix("https://doi.org/").removeprefix("doi.org/")
        if not clean.startswith("10."):
            return None
        return await self._get(f"/works/{quote(clean, safe='/-._;()')}")

    async def search_by_title(self, title: str, *, rows: int = 3) -> dict[str, Any] | None:
        title = title.strip()
        if len(title) < 8:
            return None
        message = await self._get(
            "/works",
            params={"query.bibliographic": title, "rows": str(rows)},
        )
        if not message:
            return None
        items = message.get("items") or []
        return items[0] if items else None
