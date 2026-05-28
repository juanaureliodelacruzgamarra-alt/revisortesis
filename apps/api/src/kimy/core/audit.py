"""Audit middleware.

Captures every mutating HTTP call (POST/PUT/PATCH/DELETE) into ``audit_logs``.
Read-only requests (GET/HEAD/OPTIONS) are skipped to keep volume manageable.

Insertion is fire-and-forget on its own DB session — a failure to audit MUST
NOT fail the request. We also resolve the actor by decoding the bearer token
ourselves (cheaper than going through deps).
"""
from __future__ import annotations

import logging
import time
from uuid import UUID

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from kimy.core.security import decode_token
from kimy.db.session import AsyncSessionLocal
from kimy.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Paths we always skip (high volume / low signal).
_SKIPPED_PATHS = {"/health", "/", "/openapi.json", "/docs", "/redoc"}

# We only audit mutations.
_AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _extract_actor(authorization: str | None) -> tuple[UUID | None, str | None]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None, None
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token, expected_type="access")
        return UUID(payload["sub"]), payload.get("role")
    except (jwt.PyJWTError, KeyError, ValueError):
        return None, None


async def _persist(
    *,
    actor_id: UUID | None,
    actor_role: str | None,
    method: str,
    path: str,
    status_code: int,
    duration_ms: int,
    ip: str | None,
    user_agent: str | None,
) -> None:
    try:
        async with AsyncSessionLocal() as session:
            session.add(
                AuditLog(
                    actor_id=actor_id,
                    actor_role=actor_role,
                    method=method,
                    path=path[:500],
                    status_code=status_code,
                    duration_ms=duration_ms,
                    ip=ip,
                    user_agent=user_agent[:500] if user_agent else None,
                )
            )
            await session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("audit log persistence failed")


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if (
            request.method not in _AUDITED_METHODS
            or request.url.path in _SKIPPED_PATHS
        ):
            return await call_next(request)

        started = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = int((time.perf_counter() - started) * 1000)

        actor_id, actor_role = _extract_actor(request.headers.get("authorization"))
        await _persist(
            actor_id=actor_id,
            actor_role=actor_role,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return response
