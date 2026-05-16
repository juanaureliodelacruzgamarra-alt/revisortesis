from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SettingOut(BaseModel):
    """Generic key/value system setting (merged with code defaults)."""

    model_config = ConfigDict(from_attributes=False)

    key: str
    value: dict[str, Any]
    updated_at: datetime | None = None
    updated_by: UUID | None = None


class FineTuningConfigPatch(BaseModel):
    min_examples: int | None = Field(default=None, ge=1, le=100_000)
