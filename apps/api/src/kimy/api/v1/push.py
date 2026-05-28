"""Push token registration for the Expo mobile client.

Endpoints:
- ``POST   /api/v1/push/register``   register / upsert the caller's Expo token.
- ``DELETE /api/v1/push/{token}``    unregister (logout / device-uninstall).
- ``GET    /api/v1/push/me``         list the caller's registered tokens.

Actual delivery (push send) is left to a future helper that wraps
``expo-server-sdk-python``. We persist the tokens now so deliveries can be sent
in batches when needed.
"""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select

from kimy.core.deps import CurrentUser, SessionDep
from kimy.models.push_token import PushToken
from kimy.schemas.push import PushTokenOut, PushTokenRegister

router = APIRouter(prefix="/push", tags=["push"])


@router.post(
    "/register",
    response_model=PushTokenOut,
    status_code=status.HTTP_201_CREATED,
)
async def register_token(
    payload: PushTokenRegister,
    session: SessionDep,
    user: CurrentUser,
) -> PushTokenOut:
    stmt = select(PushToken).where(PushToken.expo_token == payload.expo_token)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    now = datetime.now(UTC)
    if existing is None:
        token = PushToken(
            user_id=user.id,
            expo_token=payload.expo_token,
            device_label=payload.device_label,
            last_seen=now,
        )
        session.add(token)
    else:
        # Re-bind to the current caller (handles user-switch on the same device)
        # and refresh metadata.
        existing.user_id = user.id
        existing.device_label = payload.device_label or existing.device_label
        existing.last_seen = now
        token = existing
    await session.commit()
    await session.refresh(token)
    return PushTokenOut.model_validate(token)


@router.get("/me", response_model=list[PushTokenOut])
async def list_my_tokens(session: SessionDep, user: CurrentUser) -> list[PushTokenOut]:
    stmt = (
        select(PushToken)
        .where(PushToken.user_id == user.id)
        .order_by(PushToken.last_seen.desc().nulls_last())
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return [PushTokenOut.model_validate(r) for r in rows]


@router.delete("/{expo_token}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_token(
    expo_token: str, session: SessionDep, user: CurrentUser
) -> None:
    # Only allow deleting your own tokens.
    stmt = select(PushToken).where(
        PushToken.expo_token == expo_token, PushToken.user_id == user.id
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="token not found")
    await session.execute(delete(PushToken).where(PushToken.id == row.id))
    await session.commit()
