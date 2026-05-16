from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from kimy.db.base import Base


class SystemSetting(Base):
    """Single-row-per-key system configuration, mutable at runtime.

    Used for the AI active-model toggle and any other operational flag the
    coordinator/admin needs to flip without redeploys.
    """

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )


# Well-known keys + sane defaults — kept in code so callers don't need to
# know what JSON shape to write.
KEY_AI_MODEL_PREFERENCE = "ai.model_preference"
DEFAULT_AI_MODEL_PREFERENCE: dict[str, Any] = {
    "provider": "gemini",                # "gemini" (primary) | "anthropic" (legacy)
    "model": "gemini-2.0-flash",         # active model for the chosen provider
    "fine_tuned_model": None,            # reserved — Gemini tuning not wired
    "use_fine_tuned": False,             # A/B switch (kept for forward compat)
}

KEY_FINE_TUNING_CONFIG = "ai.fine_tuning"
DEFAULT_FINE_TUNING_CONFIG: dict[str, Any] = {
    "min_examples": 500,             # alert threshold
}
