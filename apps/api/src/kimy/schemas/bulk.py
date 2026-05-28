from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from kimy.models.submission import SubmissionStatus


class BulkRequest(BaseModel):
    operation: Literal["reprocess_ai", "set_status", "assign_advisor"]
    submission_ids: list[UUID] = Field(min_length=1, max_length=200)

    # Operation-specific payload — only one is required per call.
    status: SubmissionStatus | None = None
    advisor_id: UUID | None = None


class BulkOutcomeOut(BaseModel):
    submission_id: UUID
    ok: bool
    detail: str


class BulkResponse(BaseModel):
    operation: str
    total: int
    succeeded: int
    failed: int
    outcomes: list[BulkOutcomeOut]
