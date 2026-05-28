from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from kimy.models.plagiarism_match import PlagiarismSource, PlagiarismStatus


class ChunkPreview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    section: str | None
    text: str
    char_count: int


class PlagiarismMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    similarity: float
    source: PlagiarismSource
    status: PlagiarismStatus
    created_at: datetime

    matched_version_id: UUID
    matched_student_name: str
    matched_submission_title: str

    source_chunk: ChunkPreview
    matched_chunk: ChunkPreview
