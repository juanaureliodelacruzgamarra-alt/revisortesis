from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PushTokenRegister(BaseModel):
    expo_token: str = Field(min_length=10, max_length=255)
    device_label: str | None = Field(default=None, max_length=255)


class PushTokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    expo_token: str
    device_label: str | None
    last_seen: datetime | None
    created_at: datetime
