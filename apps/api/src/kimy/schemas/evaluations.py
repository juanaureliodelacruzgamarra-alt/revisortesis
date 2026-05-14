from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from kimy.models.ai_finding import FindingSeverity, FindingType, HumanAction


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    section: str | None
    page_approx: int | None
    type: FindingType
    severity: FindingSeverity
    description: str
    instruction: str
    example: str
    recommendation: str

    human_action: HumanAction | None
    human_comment: str | None
    human_severity_override: FindingSeverity | None
    reviewed_by: UUID | None
    reviewed_at: datetime | None

    created_at: datetime


class EvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_id: UUID
    backend: str
    model: str
    prompt_version: str
    duration_ms: int

    structure_score: float
    content_score: float
    form_score: float
    originality_score: float
    total_percentage: float
    decimal_grade: float
    executive_summary: str
    created_at: datetime

    findings: list[FindingOut]


class FindingHumanPatch(BaseModel):
    action: HumanAction
    comment: str | None = Field(default=None, max_length=4000)
    severity_override: FindingSeverity | None = None
