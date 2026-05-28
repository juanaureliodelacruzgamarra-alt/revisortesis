from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.submission_version import SubmissionVersion


class CitationStatus(str, enum.Enum):
    pending = "pending"            # not yet checked
    verified = "verified"          # found in CrossRef with matching metadata
    partial = "partial"            # found but year/authors diverge slightly
    not_found = "not_found"        # no CrossRef hit
    hallucinated = "hallucinated"  # not found AND looks suspicious / clearly fake


class Citation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "citations"

    version_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("submission_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    authors: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    journal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)

    crossref_status: Mapped[CitationStatus] = mapped_column(
        Enum(CitationStatus, name="citation_status"),
        nullable=False,
        default=CitationStatus.pending,
        index=True,
    )
    crossref_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    crossref_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    version: Mapped[SubmissionVersion] = relationship()
