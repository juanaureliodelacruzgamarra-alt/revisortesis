from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from kimy.models.submission import SubmissionStatus
from kimy.models.submission_version import VersionParsingStatus
from kimy.schemas.programs import ProgramOut


class SubmissionCreate(BaseModel):
    program_id: UUID
    title: str = Field(min_length=2, max_length=255)
    chapter: str | None = Field(default=None, max_length=100)


class SubmissionStudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str


class SubmissionVersionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    comment: str | None
    original_filename: str
    mime_type: str
    file_size_bytes: int
    page_count: int
    parsing_status: VersionParsingStatus
    parsing_error: str | None
    created_at: datetime


class SubmissionVersionDetail(SubmissionVersionSummary):
    structure_json: dict[str, Any] | None


class SubmissionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    chapter: str | None
    status: SubmissionStatus
    program_id: UUID
    template_id: UUID | None
    advisor_id: UUID | None
    student: SubmissionStudentOut
    program: ProgramOut
    created_at: datetime
    latest_version_number: int | None = None  # populated by service
    latest_version_status: VersionParsingStatus | None = None


class SubmissionDetail(SubmissionSummary):
    versions: list[SubmissionVersionSummary]
