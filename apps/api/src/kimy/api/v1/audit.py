"""Audit log listing — admin only."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from kimy.core.deps import SessionDep, require_roles
from kimy.models.audit_log import AuditLog
from kimy.models.user import UserRole
from kimy.schemas.audit import AuditLogOut

router = APIRouter(
    prefix="/admin/audit",
    tags=["admin", "audit"],
    dependencies=[Depends(require_roles(UserRole.admin))],
)


@router.get("", response_model=list[AuditLogOut])
async def list_audit(
    session: SessionDep,
    actor_id: Annotated[UUID | None, Query()] = None,
    method: Annotated[str | None, Query()] = None,
    path: Annotated[str | None, Query()] = None,
    min_status: Annotated[int | None, Query(ge=100, le=599)] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditLogOut]:
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if actor_id is not None:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if method:
        stmt = stmt.where(AuditLog.method == method.upper())
    if path:
        stmt = stmt.where(AuditLog.path.like(f"%{path}%"))
    if min_status is not None:
        stmt = stmt.where(AuditLog.status_code >= min_status)
    rows = list((await session.execute(stmt)).scalars().all())
    return [AuditLogOut.model_validate(r) for r in rows]
