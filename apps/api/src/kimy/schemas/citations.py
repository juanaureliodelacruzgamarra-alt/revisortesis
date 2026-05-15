from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from kimy.models.citation import CitationStatus


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_text: str
    title: str | None
    authors: str | None
    year: int | None
    journal: str | None
    doi: str | None
    crossref_status: CitationStatus
    crossref_message: str | None
    checked_at: datetime | None
    created_at: datetime
