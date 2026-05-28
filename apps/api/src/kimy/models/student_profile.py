from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from kimy.models.academic_program import AcademicProgram
    from kimy.models.user import User


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("academic_programs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    advisor_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    student_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped[User] = relationship(
        foreign_keys=[user_id],
        back_populates="student_profile",
    )
    program: Mapped[AcademicProgram | None] = relationship(back_populates="students")
    advisor: Mapped[User | None] = relationship(foreign_keys=[advisor_id])
