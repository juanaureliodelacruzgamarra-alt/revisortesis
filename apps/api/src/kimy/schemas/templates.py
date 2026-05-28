from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from kimy.models.template_document import TemplateParsingStatus
from kimy.schemas.programs import ProgramOut


class TemplateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    program_id: UUID
    title: str
    version: int
    description: str | None
    original_filename: str
    mime_type: str
    file_size_bytes: int
    parsing_status: TemplateParsingStatus
    parsing_error: str | None
    is_active: bool
    created_at: datetime


class TemplateDetail(TemplateSummary):
    structure_json: dict[str, Any] | None
    rubric_json: dict[str, Any] | None
    program: ProgramOut


class TemplatePatch(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    rubric_json: dict[str, Any] | None = None
