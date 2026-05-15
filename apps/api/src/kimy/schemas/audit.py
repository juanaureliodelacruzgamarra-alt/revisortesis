from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    actor_role: str | None
    method: str
    path: str
    status_code: int
    duration_ms: int
    ip: str | None
    user_agent: str | None
    created_at: datetime
