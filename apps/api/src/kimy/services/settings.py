"""Read/write helpers for the ``system_settings`` table.

Settings are keyed by well-known strings declared in ``kimy.models.system_setting``.
Reads fall back to the in-code defaults, so brand-new installs work without
seeding.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from kimy.models.system_setting import (
    DEFAULT_AI_MODEL_PREFERENCE,
    DEFAULT_FINE_TUNING_CONFIG,
    KEY_AI_MODEL_PREFERENCE,
    KEY_FINE_TUNING_CONFIG,
    SystemSetting,
)

_DEFAULTS: dict[str, dict[str, Any]] = {
    KEY_AI_MODEL_PREFERENCE: DEFAULT_AI_MODEL_PREFERENCE,
    KEY_FINE_TUNING_CONFIG: DEFAULT_FINE_TUNING_CONFIG,
}


async def get(session: AsyncSession, key: str) -> dict[str, Any]:
    """Return the stored value merged on top of the default."""
    default = _DEFAULTS.get(key, {}).copy()
    row = await session.get(SystemSetting, key)
    if row is None:
        return default
    return {**default, **(row.value or {})}


async def upsert(
    session: AsyncSession,
    key: str,
    value: dict[str, Any],
    *,
    updated_by: UUID | None,
) -> dict[str, Any]:
    row = await session.get(SystemSetting, key)
    now = datetime.now(UTC)
    if row is None:
        row = SystemSetting(
            key=key,
            value=value,
            updated_at=now,
            updated_by=updated_by,
        )
        session.add(row)
    else:
        row.value = value
        row.updated_at = now
        row.updated_by = updated_by
    await session.commit()
    await session.refresh(row)
    return row.value
