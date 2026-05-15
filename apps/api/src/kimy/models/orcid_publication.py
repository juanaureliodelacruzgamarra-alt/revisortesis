from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kimy.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from kimy.models.document_chunk import EMBEDDING_DIM

if TYPE_CHECKING:
    from kimy.models.advisor_profile import AdvisorProfile


class OrcidPublication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A publication fetched from an advisor's ORCID record."""

    __tablename__ = "orcid_publications"
    __table_args__ = (
        UniqueConstraint(
            "advisor_id", "put_code", name="uq_orcid_publications_advisor_put_code"
        ),
    )

    advisor_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("advisor_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    put_code: Mapped[str] = mapped_column(String(50), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    journal: Mapped[str | None] = mapped_column(String(500), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)

    advisor: Mapped[AdvisorProfile] = relationship(back_populates="publications")
