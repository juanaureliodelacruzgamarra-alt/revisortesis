from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.student_profile import StudentProfile


class ProgramLevel(str, enum.Enum):
    undergraduate = "undergraduate"
    masters = "masters"
    doctorate = "doctorate"


class AcademicProgram(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "academic_programs"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    level: Mapped[ProgramLevel] = mapped_column(
        Enum(ProgramLevel, name="program_level"),
        nullable=False,
    )

    students: Mapped[list[StudentProfile]] = relationship(back_populates="program")

    def __repr__(self) -> str:
        return f"<AcademicProgram {self.code} {self.level.value}>"
