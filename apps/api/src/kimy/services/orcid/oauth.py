"""ORCID OAuth 2.0 client.

Two modes:
- **real**: when ``settings.orcid_client_id`` and ``settings.orcid_client_secret``
  are configured, use the actual ORCID OAuth flow against sandbox.orcid.org
  (or orcid.org if ``orcid_sandbox`` is false).
- **stub**: otherwise return a deterministic fake authorisation that produces a
  fake ORCID iD and a small canned publication list — lets the rest of the
  pipeline (publications, embeddings, advisor-fit) be exercised without an
  ORCID developer account.

Caller is responsible for CSRF state generation/verification (we just round-trip
the value back to ORCID's ``state`` param and check equality on the callback).
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from kimy.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OrcidTokenResult:
    orcid_id: str
    access_token: str
    refresh_token: str | None
    name: str | None  # may not be present in public flow
    backend: str       # "real" | "stub"


SCOPE = "/authenticate"  # ORCID public API for basic identity & public works


def _base_authorize() -> str:
    settings = get_settings()
    host = "sandbox.orcid.org" if settings.orcid_sandbox else "orcid.org"
    return f"https://{host}/oauth/authorize"


def _base_token() -> str:
    settings = get_settings()
    host = "sandbox.orcid.org" if settings.orcid_sandbox else "orcid.org"
    return f"https://{host}/oauth/token"


def is_real_mode() -> bool:
    settings = get_settings()
    return bool(settings.orcid_client_id and settings.orcid_client_secret)


def build_authorize_url(state: str) -> str:
    settings = get_settings()
    if not is_real_mode():
        # In stub mode we don't bounce through ORCID at all — we'll surface a
        # synthetic callback URL that the frontend can hit directly.
        params = {"state": state, "code": "stub-code"}
        return f"{settings.orcid_redirect_uri}?{urlencode(params)}"

    params = {
        "client_id": settings.orcid_client_id,
        "response_type": "code",
        "scope": SCOPE,
        "redirect_uri": settings.orcid_redirect_uri,
        "state": state,
    }
    return f"{_base_authorize()}?{urlencode(params)}"


async def exchange_code(code: str) -> OrcidTokenResult:
    if not is_real_mode():
        return _stub_exchange(code)

    settings = get_settings()
    data = {
        "client_id": settings.orcid_client_id,
        "client_secret": settings.orcid_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.orcid_redirect_uri,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            _base_token(),
            data=data,
            headers={"Accept": "application/json"},
        )
    if not response.is_success:
        raise OrcidAuthError(
            f"ORCID token exchange failed: {response.status_code} {response.text[:200]}"
        )
    payload: dict[str, Any] = response.json()
    orcid_id = payload.get("orcid") or ""
    access_token = payload.get("access_token") or ""
    if not orcid_id or not access_token:
        raise OrcidAuthError("ORCID token response missing orcid or access_token")
    return OrcidTokenResult(
        orcid_id=orcid_id,
        access_token=access_token,
        refresh_token=payload.get("refresh_token"),
        name=payload.get("name"),
        backend="real",
    )


def _stub_exchange(code: str) -> OrcidTokenResult:
    """Deterministic fake — useful for dev. The ORCID iD is derived from the
    code so different test users get different IDs."""
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
    block = lambda i: digest[i : i + 4].upper()  # noqa: E731
    fake_orcid = f"0000-{block(0)[:4]}-{block(4)[:4]}-{block(8)[:4]}"
    return OrcidTokenResult(
        orcid_id=fake_orcid,
        access_token=f"stub.{digest[:32]}",
        refresh_token=f"refresh.stub.{digest[32:64]}",
        name="Dev ORCID Advisor",
        backend="stub",
    )


class OrcidAuthError(Exception):
    pass
