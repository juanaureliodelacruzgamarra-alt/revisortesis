from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.user import User


class PushToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Expo push notification token for a user's device.

    One row per (user, device) — same user can have multiple devices, the same
    device should only have one active token.
    """

    __tablename__ = "push_tokens"
    __table_args__ = (
        UniqueConstraint("expo_token", name="uq_push_tokens_expo_token"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expo_token: Mapped[str] = mapped_column(String(255), nullable=False)
    device_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship()
