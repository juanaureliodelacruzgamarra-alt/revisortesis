"""Expo push notification delivery.

Two layers:
- ``deliver(...)`` is the low-level batch sender against Expo's push API. It
  knows about chunking, the ``DeviceNotRegistered`` error (so we prune dead
  tokens) and best-effort retries.
- ``notify_user(...)`` is the high-level helper everything else calls. It looks
  up the user's tokens, drops obviously-stale ones, and runs ``deliver`` in a
  thread (the SDK is sync and we live in async land).

Failures NEVER raise — pushes are best-effort, the rest of the pipeline must
keep running if Expo's infra blips.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.db.session import AsyncSessionLocal
from kimy.models.push_token import PushToken

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PushPayload:
    title: str
    body: str
    data: dict[str, Any]  # arbitrary payload — the mobile app reads `submission_id` etc.


def _is_valid_expo_token(token: str) -> bool:
    """Expo tokens look like ``ExponentPushToken[xxxxxx]`` or ``ExpoPushToken[…]``."""
    return token.startswith(("ExponentPushToken[", "ExpoPushToken["))


def _send_blocking(tokens: list[str], payload: PushPayload) -> list[str]:
    """Synchronous Expo SDK call. Returns the subset of tokens that look dead
    (``DeviceNotRegistered``) and should be pruned. Never raises."""
    if not tokens:
        return []
    try:
        from exponent_server_sdk import (
            DeviceNotRegisteredError,
            PushClient,
            PushMessage,
            PushServerError,
            PushTicketError,
        )
        from requests.exceptions import ConnectionError as RequestsConnectionError
        from requests.exceptions import HTTPError
    except ImportError as exc:
        logger.warning("exponent-server-sdk not installed: %s — push skipped", exc)
        return []

    messages = [
        PushMessage(
            to=token,
            title=payload.title,
            body=payload.body,
            data=payload.data,
            sound="default",
        )
        for token in tokens
    ]
    dead: list[str] = []
    client = PushClient()
    try:
        tickets = client.publish_multiple(messages)
    except (PushServerError, ConnectionError, RequestsConnectionError, HTTPError) as exc:
        logger.warning("expo push delivery failed entirely: %s", exc)
        return []

    for token, ticket in zip(tokens, tickets, strict=True):
        try:
            ticket.validate_response()
        except DeviceNotRegisteredError:
            dead.append(token)
        except PushTicketError as exc:
            logger.warning("expo push ticket for %s: %s", token[:24], exc)
        except Exception:  # noqa: BLE001
            logger.exception("unexpected expo push error for %s", token[:24])
    return dead


async def _load_tokens(session: AsyncSession, user_id: UUID) -> list[PushToken]:
    stmt = select(PushToken).where(PushToken.user_id == user_id)
    return list((await session.execute(stmt)).scalars().all())


async def _prune_dead(session: AsyncSession, dead_tokens: list[str]) -> None:
    if not dead_tokens:
        return
    await session.execute(
        delete(PushToken).where(PushToken.expo_token.in_(dead_tokens))
    )
    await session.commit()
    logger.info("pruned %d dead push tokens", len(dead_tokens))


async def notify_user(user_id: UUID, payload: PushPayload) -> None:
    """Best-effort push to every device the user has registered. Never raises."""
    try:
        async with AsyncSessionLocal() as session:
            rows = await _load_tokens(session, user_id)
        tokens = [r.expo_token for r in rows if _is_valid_expo_token(r.expo_token)]
        if not tokens:
            return
        # Run the sync SDK call off the event loop.
        dead = await asyncio.to_thread(_send_blocking, tokens, payload)
        if dead:
            async with AsyncSessionLocal() as session:
                await _prune_dead(session, dead)
    except Exception:  # noqa: BLE001
        logger.exception("notify_user crashed for user_id=%s", user_id)
