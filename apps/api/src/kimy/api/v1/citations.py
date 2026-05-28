from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from kimy.core.deps import CurrentUser, SessionDep
from kimy.models.citation import Citation
from kimy.schemas.citations import CitationOut
from kimy.services import submissions as submissions_service

router = APIRouter(tags=["citations"])


@router.get(
    "/submissions/{submission_id}/versions/{version_id}/citations",
    response_model=list[CitationOut],
)
async def list_citations(
    submission_id: UUID,
    version_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> list[CitationOut]:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="submission not found")
    if not submissions_service.can_access(submission, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if not any(v.id == version_id for v in submission.versions):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="version not found")

    stmt = (
        select(Citation)
        .where(Citation.version_id == version_id)
        .order_by(Citation.created_at)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    return [CitationOut.model_validate(r) for r in rows]
