from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.document_chunk import DocumentChunk
    from kimy.models.submission_version import SubmissionVersion
    from kimy.models.user import User


class PlagiarismSource(str, enum.Enum):
    intra = "intra"            # similarity vs another submission in the same program
    copyleaks = "copyleaks"    # external service (future)


class PlagiarismStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    dismissed = "dismissed"


class PlagiarismMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plagiarism_matches"

    version_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("submission_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matched_version_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("submission_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_chunk_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    matched_chunk_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )

    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[PlagiarismSource] = mapped_column(
        Enum(PlagiarismSource, name="plagiarism_source"),
        nullable=False,
        default=PlagiarismSource.intra,
    )
    status: Mapped[PlagiarismStatus] = mapped_column(
        Enum(PlagiarismStatus, name="plagiarism_status"),
        nullable=False,
        default=PlagiarismStatus.pending,
        index=True,
    )

    reviewed_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    version: Mapped[SubmissionVersion] = relationship(foreign_keys=[version_id])
    matched_version: Mapped[SubmissionVersion] = relationship(
        foreign_keys=[matched_version_id]
    )
    source_chunk: Mapped[DocumentChunk] = relationship(foreign_keys=[source_chunk_id])
    matched_chunk: Mapped[DocumentChunk] = relationship(
        foreign_keys=[matched_chunk_id]
    )
    reviewer: Mapped[User | None] = relationship()
