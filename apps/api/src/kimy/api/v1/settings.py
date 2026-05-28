"""Admin system settings — read all known keys, update fine-tuning config.

The AI model preference lives in ``api/v1/fine_tuning.py`` (kept there to avoid
breaking existing clients). This router complements it with:

- ``GET  /admin/settings``                       — read all known keys at once
- ``GET  /admin/settings/fine-tuning``           — read fine-tuning config
- ``PUT  /admin/settings/fine-tuning``           — update fine-tuning config
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select

from kimy.core.deps import CurrentUser, SessionDep, require_roles
from kimy.models.system_setting import (
    KEY_AI_MODEL_PREFERENCE,
    KEY_FINE_TUNING_CONFIG,
    SystemSetting,
)
from kimy.models.user import UserRole
from kimy.schemas.settings import FineTuningConfigPatch, SettingOut
from kimy.services import settings as settings_service

router = APIRouter(
    prefix="/admin/settings",
    tags=["admin", "settings"],
    dependencies=[Depends(require_roles(UserRole.admin))],
)


_KNOWN_KEYS = [KEY_AI_MODEL_PREFERENCE, KEY_FINE_TUNING_CONFIG]


@router.get("", response_model=list[SettingOut])
async def list_settings(session: SessionDep) -> list[SettingOut]:
    stmt = select(SystemSetting).where(SystemSetting.key.in_(_KNOWN_KEYS))
    rows = {r.key: r for r in (await session.execute(stmt)).scalars().all()}

    out: list[SettingOut] = []
    for key in _KNOWN_KEYS:
        merged = await settings_service.get(session, key)
        row = rows.get(key)
        out.append(
            SettingOut(
                key=key,
                value=merged,
                updated_at=row.updated_at if row else None,
                updated_by=row.updated_by if row else None,
            )
        )
    return out


@router.get("/fine-tuning", response_model=SettingOut)
async def get_fine_tuning(session: SessionDep) -> SettingOut:
    cfg = await settings_service.get(session, KEY_FINE_TUNING_CONFIG)
    row = await session.get(SystemSetting, KEY_FINE_TUNING_CONFIG)
    return SettingOut(
        key=KEY_FINE_TUNING_CONFIG,
        value=cfg,
        updated_at=row.updated_at if row else None,
        updated_by=row.updated_by if row else None,
    )


@router.put("/fine-tuning", response_model=SettingOut)
async def set_fine_tuning(
    payload: FineTuningConfigPatch,
    session: SessionDep,
    user: CurrentUser,
) -> SettingOut:
    cfg: dict[str, Any] = await settings_service.get(session, KEY_FINE_TUNING_CONFIG)
    if payload.min_examples is not None:
        cfg["min_examples"] = int(payload.min_examples)
    new = await settings_service.upsert(
        session, KEY_FINE_TUNING_CONFIG, cfg, updated_by=user.id
    )
    row = await session.get(SystemSetting, KEY_FINE_TUNING_CONFIG)
    return SettingOut(
        key=KEY_FINE_TUNING_CONFIG,
        value=new,
        updated_at=row.updated_at if row else None,
        updated_by=row.updated_by if row else None,
    )
