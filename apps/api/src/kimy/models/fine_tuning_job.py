from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from kimy.models.user import User


class FineTuningStatus(str, enum.Enum):
    dataset_ready = "dataset_ready"   # JSONL exported, not yet uploaded
    uploading = "uploading"           # pushing the JSONL to OpenAI
    queued = "queued"                 # OpenAI received it, job created
    running = "running"               # OpenAI is training
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class FineTuningJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fine_tuning_jobs"

    status: Mapped[FineTuningStatus] = mapped_column(
        Enum(FineTuningStatus, name="fine_tuning_status"),
        nullable=False,
        default=FineTuningStatus.dataset_ready,
        index=True,
    )

    dataset_path: Mapped[str] = mapped_column(String(512), nullable=False)
    examples_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    base_model: Mapped[str] = mapped_column(String(100), nullable=False)
    openai_file_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    openai_job_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, unique=True
    )
    fine_tuned_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    creator: Mapped[User | None] = relationship()
