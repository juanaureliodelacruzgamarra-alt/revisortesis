from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from kimy.core.deps import CurrentUser, SessionDep, require_roles
from kimy.models.submission import Submission
from kimy.models.submission_version import VersionParsingStatus
from kimy.models.user import UserRole
from kimy.schemas.submissions import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionSummary,
    SubmissionVersionDetail,
    SubmissionVersionSummary,
)
from kimy.services import programs as programs_service
from kimy.services import storage
from kimy.services import submissions as submissions_service
from kimy.services.ai import pipeline as ai_pipeline

router = APIRouter(prefix="/submissions", tags=["submissions"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


def _to_summary(s: Submission) -> SubmissionSummary:
    latest = submissions_service.latest_version(s)
    return SubmissionSummary(
        id=s.id,
        title=s.title,
        chapter=s.chapter,
        status=s.status,
        program_id=s.program_id,
        template_id=s.template_id,
        advisor_id=s.advisor_id,
        student=s.student,  # type: ignore[arg-type]
        program=s.program,  # type: ignore[arg-type]
        created_at=s.created_at,
        latest_version_number=latest.version_number if latest else None,
        latest_version_status=latest.parsing_status if latest else None,
    )


def _to_detail(s: Submission) -> SubmissionDetail:
    summary = _to_summary(s)
    return SubmissionDetail(
        **summary.model_dump(),
        versions=[SubmissionVersionSummary.model_validate(v) for v in s.versions],
    )


def _ensure_can_access(submission: Submission, user) -> None:
    if not submissions_service.can_access(submission, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden",
        )


@router.get("", response_model=list[SubmissionSummary])
async def list_submissions(
    session: SessionDep, user: CurrentUser
) -> list[SubmissionSummary]:
    items = await submissions_service.list_for_user(session, user)
    return [_to_summary(s) for s in items]


@router.post(
    "",
    response_model=SubmissionDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.student))],
)
async def create_submission(
    payload: SubmissionCreate, session: SessionDep, user: CurrentUser
) -> SubmissionDetail:
    program = await programs_service.get_program(session, payload.program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="program not found"
        )
    submission = await submissions_service.create_submission(
        session,
        student_id=user.id,
        program_id=payload.program_id,
        title=payload.title,
        chapter=payload.chapter,
    )
    return _to_detail(submission)


@router.get("/{submission_id}", response_model=SubmissionDetail)
async def get_submission(
    submission_id: UUID, session: SessionDep, user: CurrentUser
) -> SubmissionDetail:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="submission not found"
        )
    _ensure_can_access(submission, user)
    return _to_detail(submission)


@router.post(
    "/{submission_id}/versions",
    response_model=SubmissionVersionDetail,
    status_code=status.HTTP_201_CREATED,
)
async def upload_version(
    submission_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    comment: Annotated[str | None, Form(max_length=2000)] = None,
) -> SubmissionVersionDetail:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="submission not found"
        )

    if user.role == UserRole.student and submission.student_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="students can only upload to their own submissions",
        )
    if user.role in {UserRole.advisor, UserRole.coordinator}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="only students can upload new versions",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"file exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit",
        )

    try:
        version = await submissions_service.upload_version(
            session,
            submission=submission,
            filename=file.filename or "upload.bin",
            content=content,
            mime_type=file.content_type or "application/octet-stream",
            comment=comment,
        )
    except submissions_service.UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc

    if version.parsing_status == VersionParsingStatus.ai_queued:
        background.add_task(ai_pipeline.background_runner, version.id)

    return SubmissionVersionDetail.model_validate(version)


@router.get(
    "/{submission_id}/versions/{version_id}",
    response_model=SubmissionVersionDetail,
)
async def get_version(
    submission_id: UUID,
    version_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> SubmissionVersionDetail:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="submission not found"
        )
    _ensure_can_access(submission, user)
    version = next(
        (v for v in submission.versions if v.id == version_id), None
    )
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="version not found"
        )
    return SubmissionVersionDetail.model_validate(version)


@router.get("/{submission_id}/versions/{version_id}/file")
async def download_version(
    submission_id: UUID,
    version_id: UUID,
    session: SessionDep,
    user: CurrentUser,
) -> FileResponse:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="submission not found"
        )
    _ensure_can_access(submission, user)
    version = next(
        (v for v in submission.versions if v.id == version_id), None
    )
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="version not found"
        )
    path = storage.resolve(version.storage_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="file missing on disk"
        )
    return FileResponse(
        path=path,
        filename=version.original_filename,
        media_type=version.mime_type,
    )


@router.patch(
    "/{submission_id}/advisor",
    response_model=SubmissionDetail,
    dependencies=[Depends(require_roles(UserRole.coordinator, UserRole.admin))],
)
async def assign_advisor(
    submission_id: UUID,
    session: SessionDep,
    advisor_id: Annotated[UUID | None, Body(embed=True)] = None,
) -> SubmissionDetail:
    submission = await submissions_service.get_submission(session, submission_id)
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="submission not found"
        )
    updated = await submissions_service.assign_advisor(
        session, submission=submission, advisor_id=advisor_id
    )
    return _to_detail(updated)
