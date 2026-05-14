from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from kimy.models.user import User


class AdvisorProfile(TimestampMixin, Base):
    __tablename__ = "advisor_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    affiliation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ORCID linking — populated in Phase 7
    orcid_id: Mapped[str | None] = mapped_column(
        String(50), nullable=True, unique=True, index=True
    )
    orcid_access_token_enc: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    orcid_refresh_token_enc: Mapped[bytes | None] = mapped_column(
        LargeBinary, nullable=True
    )
    orcid_last_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped[User] = relationship(back_populates="advisor_profile")
