from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrcidAuthorizeOut(BaseModel):
    authorize_url: str
    state: str
    mode: str  # "real" | "stub"


class OrcidLinkResult(BaseModel):
    linked: bool
    orcid_id: str | None
    affiliation: str | None
    last_sync: datetime | None
    publications_count: int
    backend: str


class OrcidStatusOut(BaseModel):
    linked: bool
    orcid_id: str | None
    affiliation: str | None
    last_sync: datetime | None
    publications_count: int


class OrcidPublicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    put_code: str
    title: str
    year: int | None
    journal: str | None
    doi: str | None
    url: str | None
    created_at: datetime
