"""Internal schemas used by the AI pipeline.

These are NOT the API response schemas (those live in kimy.schemas.evaluations).
They are the contract between the LLM output / stub output and the persistence
layer.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from kimy.models.ai_finding import FindingSeverity, FindingType


class AIScores(BaseModel):
    structure: float = Field(ge=0, le=100)
    content: float = Field(ge=0, le=100)
    form: float = Field(ge=0, le=100)
    originality: float = Field(ge=0, le=100)


class AIFindingDraft(BaseModel):
    section: str | None = None
    page_approx: int | None = None
    type: FindingType
    severity: FindingSeverity
    description: str = Field(min_length=1, max_length=2000)
    instruction: str = ""
    example: str = ""
    recommendation: str = ""


class AIEvaluationDraft(BaseModel):
    executive_summary: str
    scores: AIScores
    findings: list[AIFindingDraft]

    def total_percentage(self) -> float:
        s = self.scores
        return s.structure * 0.30 + s.content * 0.40 + s.form * 0.20 + s.originality * 0.10
