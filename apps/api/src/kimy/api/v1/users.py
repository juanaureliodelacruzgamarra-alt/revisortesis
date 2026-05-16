"""Admin user management — list / create / patch."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select

from kimy.core.deps import CurrentUser, SessionDep, require_roles
from kimy.core.security import hash_password
from kimy.models.user import User, UserRole
from kimy.schemas.users import AdminUserCreate, AdminUserOut, AdminUserPatch
from kimy.services import users as users_service

router = APIRouter(
    prefix="/admin/users",
    tags=["admin", "users"],
    dependencies=[Depends(require_roles(UserRole.admin))],
)


@router.get("", response_model=list[AdminUserOut])
async def list_users(
    session: SessionDep,
    role: Annotated[UserRole | None, Query()] = None,
    q: Annotated[str | None, Query(description="search in email/full_name")] = None,
    is_active: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[AdminUserOut]:
    stmt = select(User).order_by(User.created_at.desc()).limit(limit)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(User.email.ilike(like), User.full_name.ilike(like))
        )
    rows = list((await session.execute(stmt)).scalars().all())
    return [AdminUserOut.model_validate(r) for r in rows]


@router.post("", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate,
    session: SessionDep,
) -> AdminUserOut:
    try:
        user = await users_service.create_user(
            session,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
        )
    except users_service.EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        ) from exc
    return AdminUserOut.model_validate(user)


@router.patch("/{user_id}", response_model=AdminUserOut)
async def patch_user(
    user_id: UUID,
    payload: AdminUserPatch,
    session: SessionDep,
    current: CurrentUser,
) -> AdminUserOut:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )

    # Guard: an admin cannot lock themselves out (deactivate self or demote self).
    if user.id == current.id:
        if payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cannot deactivate yourself",
            )
        if payload.role is not None and payload.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="cannot change your own role",
            )

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)

    await session.commit()
    await session.refresh(user)
    return AdminUserOut.model_validate(user)
