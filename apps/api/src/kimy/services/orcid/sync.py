"""Sync publications from ORCID into our local DB with embeddings.

Idempotent: drops the advisor's existing publications and re-inserts. Run on
link and on any explicit "refresh" request from the advisor.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.core.crypto import decrypt, encrypt
from kimy.models.advisor_profile import AdvisorProfile
from kimy.models.orcid_publication import OrcidPublication
from kimy.services.orcid import api_client as orcid_api
from kimy.services.orcid.oauth import OrcidTokenResult
from kimy.services.plagiarism.embedder import embed_texts

logger = logging.getLogger(__name__)


async def link_advisor(
    session: AsyncSession,
    *,
    advisor_user_id: UUID,
    token: OrcidTokenResult,
) -> AdvisorProfile:
    """Persist the ORCID linkage + sync publications + embeddings."""
    profile = await session.get(AdvisorProfile, advisor_user_id)
    if profile is None:
        # The auth flow runs *after* registration, so the profile must exist.
        raise ValueError(f"AdvisorProfile {advisor_user_id} not found")

    profile.orcid_id = token.orcid_id
    profile.orcid_access_token_enc = encrypt(token.access_token)
    profile.orcid_refresh_token_enc = (
        encrypt(token.refresh_token) if token.refresh_token else None
    )

    person = await orcid_api.fetch_person(token.orcid_id, token.access_token)
    if person and person.affiliation:
        profile.affiliation = person.affiliation[:255]

    works = await orcid_api.fetch_works(token.orcid_id, token.access_token)

    # Replace prior publications atomically.
    await session.execute(
        delete(OrcidPublication).where(OrcidPublication.advisor_id == advisor_user_id)
    )
    await session.flush()

    if works:
        titles = [w.title for w in works]
        embeddings, _backend = embed_texts(titles)
        for work, vector in zip(works, embeddings, strict=True):
            session.add(
                OrcidPublication(
                    advisor_id=advisor_user_id,
                    put_code=work.put_code,
                    title=work.title,
                    year=work.year,
                    journal=work.journal,
                    doi=work.doi,
                    url=work.url,
                    embedding=vector,
                )
            )

    profile.orcid_last_sync = datetime.now(UTC)
    await session.commit()
    await session.refresh(profile)
    return profile


async def unlink_advisor(session: AsyncSession, advisor_user_id: UUID) -> bool:
    profile = await session.get(AdvisorProfile, advisor_user_id)
    if profile is None or profile.orcid_id is None:
        return False
    profile.orcid_id = None
    profile.orcid_access_token_enc = None
    profile.orcid_refresh_token_enc = None
    profile.orcid_last_sync = None
    await session.execute(
        delete(OrcidPublication).where(OrcidPublication.advisor_id == advisor_user_id)
    )
    await session.commit()
    return True


async def get_advisor_publications(
    session: AsyncSession, advisor_user_id: UUID
) -> list[OrcidPublication]:
    stmt = (
        select(OrcidPublication)
        .where(OrcidPublication.advisor_id == advisor_user_id)
        .order_by(OrcidPublication.year.desc().nulls_last(), OrcidPublication.title)
    )
    return list((await session.execute(stmt)).scalars().all())


def safe_decrypt_token(blob: bytes | None) -> str | None:
    """Return decrypted token or None — never raises."""
    if not blob:
        return None
    try:
        return decrypt(blob)
    except Exception:  # noqa: BLE001
        logger.warning("failed to decrypt ORCID token — key may have rotated")
        return None


def public_orcid_payload(profile: AdvisorProfile) -> dict[str, Any]:
    """Safe-to-return shape for endpoints (no tokens, ever)."""
    return {
        "linked": profile.orcid_id is not None,
        "orcid_id": profile.orcid_id,
        "affiliation": profile.affiliation,
        "last_sync": profile.orcid_last_sync.isoformat() if profile.orcid_last_sync else None,
    }
