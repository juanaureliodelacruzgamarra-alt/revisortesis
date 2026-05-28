from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.ai_finding import AIFinding
    from kimy.models.submission_version import SubmissionVersion


class AIEvaluation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_evaluations"

    version_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("submission_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one evaluation per version (re-runs overwrite via service)
        index=True,
    )

    # Source attribution
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    backend: Mapped[str] = mapped_column(String(20), nullable=False)  # openai|anthropic|stub
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Scores (0..100 per dimension)
    structure_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    content_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    form_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    originality_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    total_percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    decimal_grade: Mapped[float] = mapped_column(Float, nullable=False, default=0)

    executive_summary: Mapped[str] = mapped_column(String(4000), nullable=False, default="")

    version: Mapped[SubmissionVersion] = relationship()
    findings: Mapped[list[AIFinding]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan",
        order_by="AIFinding.severity_order, AIFinding.created_at",
    )
