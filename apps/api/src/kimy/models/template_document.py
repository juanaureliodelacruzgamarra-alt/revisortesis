from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.academic_program import AcademicProgram
    from kimy.models.user import User


class TemplateParsingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    parsed = "parsed"
    failed = "failed"


class TemplateDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "template_documents"
    __table_args__ = (
        UniqueConstraint(
            "program_id", "version", name="uq_template_documents_program_version"
        ),
    )

    program_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("academic_programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    parsing_status: Mapped[TemplateParsingStatus] = mapped_column(
        Enum(TemplateParsingStatus, name="template_parsing_status"),
        nullable=False,
        default=TemplateParsingStatus.pending,
    )
    parsing_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    structure_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    rubric_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    program: Mapped[AcademicProgram] = relationship()
    creator: Mapped[User] = relationship()
