from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.academic_program import AcademicProgram
    from kimy.models.submission_version import SubmissionVersion
    from kimy.models.template_document import TemplateDocument
    from kimy.models.user import User


class SubmissionStatus(str, enum.Enum):
    draft = "draft"               # created, no version yet
    in_progress = "in_progress"   # at least one version uploaded
    observed = "observed"         # advisor returned with observations
    approved = "approved"
    rejected = "rejected"


class Submission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "submissions"

    student_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("academic_programs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    template_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("template_documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    advisor_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    chapter: Mapped[str | None] = mapped_column(String(100), nullable=True)

    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        nullable=False,
        default=SubmissionStatus.draft,
        index=True,
    )

    student: Mapped[User] = relationship(foreign_keys=[student_id])
    advisor: Mapped[User | None] = relationship(foreign_keys=[advisor_id])
    program: Mapped[AcademicProgram] = relationship()
    template: Mapped[TemplateDocument | None] = relationship()
    versions: Mapped[list[SubmissionVersion]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SubmissionVersion.version_number.desc()",
    )
