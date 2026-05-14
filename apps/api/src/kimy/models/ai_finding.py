from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.ai_evaluation import AIEvaluation
    from kimy.models.user import User


class FindingSeverity(str, enum.Enum):
    critical = "critical"
    major = "major"
    minor = "minor"
    suggestion = "suggestion"


SEVERITY_ORDER: dict[FindingSeverity, int] = {
    FindingSeverity.critical: 0,
    FindingSeverity.major: 1,
    FindingSeverity.minor: 2,
    FindingSeverity.suggestion: 3,
}


class FindingType(str, enum.Enum):
    missing_section = "missing_section"
    structural_error = "structural_error"
    content_error = "content_error"
    form_error = "form_error"
    coherence_issue = "coherence_issue"
    suggestion = "suggestion"


class HumanAction(str, enum.Enum):
    accepted = "accepted"
    modified = "modified"
    rejected = "rejected"


class AIFinding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_findings"

    evaluation_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("ai_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    section: Mapped[str | None] = mapped_column(String(255), nullable=True)
    page_approx: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type: Mapped[FindingType] = mapped_column(
        Enum(FindingType, name="finding_type"), nullable=False
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity, name="finding_severity"), nullable=False, index=True
    )
    severity_order: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    instruction: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    example: Mapped[str] = mapped_column(String(4000), nullable=False, default="")
    recommendation: Mapped[str] = mapped_column(String(2000), nullable=False, default="")

    # Human review (feedback loop for Fase 10 fine-tuning)
    human_action: Mapped[HumanAction | None] = mapped_column(
        Enum(HumanAction, name="finding_human_action"),
        nullable=True,
        index=True,
    )
    human_comment: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    human_severity_override: Mapped[FindingSeverity | None] = mapped_column(
        Enum(FindingSeverity, name="finding_severity_override"),
        nullable=True,
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    evaluation: Mapped[AIEvaluation] = relationship(back_populates="findings")
    reviewer: Mapped[User | None] = relationship()
