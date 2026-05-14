from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.submission import Submission, SubmissionStatus
from kimy.models.submission_version import SubmissionVersion, VersionParsingStatus
from kimy.models.template_document import TemplateDocument
from kimy.models.user import User, UserRole
from kimy.services import storage
from kimy.services.documents.extractor import extract
from kimy.services.documents.structure_parser import parse_structure

logger = logging.getLogger(__name__)


class ProgramNotFoundError(Exception):
    pass


class SubmissionNotFoundError(Exception):
    pass


class NoActiveTemplateError(Exception):
    pass


class UnsupportedFileTypeError(Exception):
    pass


class ForbiddenSubmissionAccessError(Exception):
    pass


_ALLOWED_EXTENSIONS = {"docx", "pdf"}
_ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _ext_from_filename(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


async def _resolve_active_template(
    session: AsyncSession, program_id: UUID
) -> TemplateDocument | None:
    stmt = (
        select(TemplateDocument)
        .where(
            TemplateDocument.program_id == program_id,
            TemplateDocument.is_active.is_(True),
        )
        .order_by(TemplateDocument.version.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def create_submission(
    session: AsyncSession,
    *,
    student_id: UUID,
    program_id: UUID,
    title: str,
    chapter: str | None,
) -> Submission:
    template = await _resolve_active_template(session, program_id)
    submission = Submission(
        student_id=student_id,
        program_id=program_id,
        template_id=template.id if template else None,
        title=title.strip(),
        chapter=chapter.strip() if chapter else None,
        status=SubmissionStatus.draft,
    )
    session.add(submission)
    await session.commit()
    return await get_submission(session, submission.id)  # type: ignore[return-value]


async def get_submission(
    session: AsyncSession, submission_id: UUID
) -> Submission | None:
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.program),
            selectinload(Submission.versions),
        )
        .where(Submission.id == submission_id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def can_access(submission: Submission, user: User) -> bool:
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.coordinator:
        return True
    if user.role == UserRole.advisor:
        return submission.advisor_id == user.id
    if user.role == UserRole.student:
        return submission.student_id == user.id
    return False


async def list_for_user(
    session: AsyncSession, user: User
) -> Sequence[Submission]:
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.student),
            selectinload(Submission.program),
            selectinload(Submission.versions),
        )
        .order_by(Submission.created_at.desc())
    )
    if user.role == UserRole.student:
        stmt = stmt.where(Submission.student_id == user.id)
    elif user.role == UserRole.advisor:
        stmt = stmt.where(Submission.advisor_id == user.id)
    # coordinator / admin see all
    return (await session.execute(stmt)).scalars().all()


def latest_version(submission: Submission) -> SubmissionVersion | None:
    """`Submission.versions` is ordered by version_number DESC by relationship config."""
    return submission.versions[0] if submission.versions else None


async def upload_version(
    session: AsyncSession,
    *,
    submission: Submission,
    filename: str,
    content: bytes,
    mime_type: str,
    comment: str | None,
) -> SubmissionVersion:
    ext = _ext_from_filename(filename)
    if ext not in _ALLOWED_EXTENSIONS or mime_type not in _ALLOWED_MIMES:
        raise UnsupportedFileTypeError(
            f"file '{filename}' is not a supported Word/PDF document"
        )

    stored = storage.save_bytes("submissions", content=content, extension=ext)

    next_number = (
        max((v.version_number for v in submission.versions), default=0) + 1
    )

    version = SubmissionVersion(
        submission_id=submission.id,
        version_number=next_number,
        comment=comment.strip() if comment else None,
        original_filename=filename,
        storage_path=stored.relative_path,
        mime_type=mime_type,
        file_size_bytes=stored.size_bytes,
        file_sha256=stored.sha256,
        parsing_status=VersionParsingStatus.processing,
    )
    session.add(version)
    await session.flush()

    try:
        extracted = extract(filename, content, mime_type)
        structure = parse_structure(extracted)
        version.structure_json = structure
        version.page_count = extracted.page_count
        version.parsing_status = VersionParsingStatus.parsed
        version.parsing_error = None
    except Exception as exc:  # noqa: BLE001
        version.parsing_status = VersionParsingStatus.failed
        version.parsing_error = str(exc)[:2000]
        logger.exception("submission parsing failed", extra={"version_id": str(version.id)})

    if version.parsing_status == VersionParsingStatus.parsed:
        # Placeholder for Phase 4: in Phase 4 this will enqueue a Celery task.
        version.parsing_status = VersionParsingStatus.ai_queued

    if submission.status == SubmissionStatus.draft:
        submission.status = SubmissionStatus.in_progress

    await session.commit()
    await session.refresh(version)
    return version


async def get_version(
    session: AsyncSession, version_id: UUID
) -> SubmissionVersion | None:
    return await session.get(SubmissionVersion, version_id)


async def assign_advisor(
    session: AsyncSession,
    *,
    submission: Submission,
    advisor_id: UUID | None,
) -> Submission:
    submission.advisor_id = advisor_id
    await session.commit()
    return await get_submission(session, submission.id)  # type: ignore[return-value]
