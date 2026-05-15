from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from kimy.models.fine_tuning_job import FineTuningStatus


class FineTuningStats(BaseModel):
    total_eligible: int
    by_action: dict[str, int]
    by_severity: dict[str, int]
    min_examples_threshold: int
    ready_to_export: bool       # True when total_eligible > 0
    ready_to_submit: bool       # True when total_eligible >= threshold AND OpenAI configured
    openai_available: bool


class ModelPreference(BaseModel):
    openai_model: str = Field(min_length=1)
    fine_tuned_model: str | None = None
    use_fine_tuned: bool = False


class ModelPreferencePatch(BaseModel):
    openai_model: str | None = None
    fine_tuned_model: str | None = None
    use_fine_tuned: bool | None = None


class FineTuningJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: FineTuningStatus
    examples_count: int
    base_model: str
    openai_file_id: str | None
    openai_job_id: str | None
    fine_tuned_model: str | None
    error: str | None
    dataset_path: str
    submitted_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
