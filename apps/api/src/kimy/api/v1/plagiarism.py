from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from kimy.core.deps import CurrentUser, SessionDep
from kimy.schemas.plagiarism import ChunkPreview, PlagiarismMatchOut
from kimy.services import submissions as submissions_service
from kimy.services.plagiarism import scanner

router = APIRouter(tags=["plagiarism"])


@router.get(
    "/submissions/{submission_id}/versions/{version_id}/plagiarism",
    response_model=list[PlagiarismMatchOut],
)
async def list_matches(
    submission_id: UUID,
    version_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> list[PlagiarismMatchOut]:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="submission not found"
        )
    if not submissions_service.can_access(submission, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    if not any(v.id == version_id for v in submission.versions):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="version not found"
        )

    matches = await scanner.list_matches_for_version(session, version_id)
    out: list[PlagiarismMatchOut] = []
    for m in matches:
        matched_submission = m.matched_version.submission
        # Need the student object; lazy-load via session
        student = (
            matched_submission.student
            if matched_submission and hasattr(matched_submission, "student") and matched_submission.student
            else None
        )
        student_name = student.full_name if student else "(desconocido)"
        out.append(
            PlagiarismMatchOut(
                id=m.id,
                similarity=m.similarity,
                source=m.source,
                status=m.status,
                created_at=m.created_at,
                matched_version_id=m.matched_version_id,
                matched_student_name=student_name,
                matched_submission_title=matched_submission.title if matched_submission else "(?)",
                source_chunk=ChunkPreview.model_validate(m.source_chunk),
                matched_chunk=ChunkPreview.model_validate(m.matched_chunk),
            )
        )
    return out
