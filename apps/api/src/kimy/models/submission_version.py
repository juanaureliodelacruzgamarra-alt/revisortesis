from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.submission import Submission


class VersionParsingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    parsed = "parsed"
    failed = "failed"
    ai_queued = "ai_queued"       # placeholder until Phase 4
    ai_processing = "ai_processing"
    ai_completed = "ai_completed"


class SubmissionVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "submission_versions"
    __table_args__ = (
        UniqueConstraint(
            "submission_id",
            "version_number",
            name="uq_submission_versions_submission_version",
        ),
    )

    submission_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parsing_status: Mapped[VersionParsingStatus] = mapped_column(
        Enum(VersionParsingStatus, name="version_parsing_status"),
        nullable=False,
        default=VersionParsingStatus.pending,
        index=True,
    )
    parsing_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    structure_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    submission: Mapped[Submission] = relationship(back_populates="versions")
