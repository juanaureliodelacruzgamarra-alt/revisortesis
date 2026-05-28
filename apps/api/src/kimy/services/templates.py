from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from kimy.models.template_document import TemplateDocument, TemplateParsingStatus
from kimy.services import storage
from kimy.services.documents.extractor import extract
from kimy.services.documents.structure_parser import parse_structure


class ProgramNotFoundError(Exception):
    pass


class UnsupportedFileTypeError(Exception):
    pass


_ALLOWED_EXTENSIONS = {"docx", "pdf"}
_ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _ext_from_filename(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


async def _next_version(session: AsyncSession, program_id: UUID) -> int:
    stmt = select(func.max(TemplateDocument.version)).where(
        TemplateDocument.program_id == program_id
    )
    latest = (await session.execute(stmt)).scalar_one_or_none()
    return (latest or 0) + 1


async def upload_template(
    session: AsyncSession,
    *,
    program_id: UUID,
    title: str,
    description: str | None,
    filename: str,
    content: bytes,
    mime_type: str,
    created_by: UUID,
) -> TemplateDocument:
    ext = _ext_from_filename(filename)
    if ext not in _ALLOWED_EXTENSIONS or mime_type not in _ALLOWED_MIMES:
        raise UnsupportedFileTypeError(
            f"file '{filename}' is not a supported Word/PDF document"
        )

    stored = storage.save_bytes("templates", content=content, extension=ext)

    template = TemplateDocument(
        program_id=program_id,
        title=title.strip(),
        description=description.strip() if description else None,
        version=await _next_version(session, program_id),
        original_filename=filename,
        storage_path=stored.relative_path,
        mime_type=mime_type,
        file_size_bytes=stored.size_bytes,
        file_sha256=stored.sha256,
        parsing_status=TemplateParsingStatus.processing,
        created_by=created_by,
        is_active=False,
    )
    session.add(template)
    await session.flush()

    try:
        extracted = extract(filename, content, mime_type)
        structure = parse_structure(extracted)
        template.structure_json = structure
        template.parsing_status = TemplateParsingStatus.parsed
        template.parsing_error = None
    except Exception as exc:  # noqa: BLE001 - we want to capture any failure here
        template.parsing_status = TemplateParsingStatus.failed
        template.parsing_error = str(exc)[:2000]

    await session.commit()
    await session.refresh(template)
    return template


async def list_templates(
    session: AsyncSession,
    *,
    program_id: UUID | None = None,
) -> Sequence[TemplateDocument]:
    stmt = (
        select(TemplateDocument)
        .options(selectinload(TemplateDocument.program))
        .order_by(desc(TemplateDocument.created_at))
    )
    if program_id is not None:
        stmt = stmt.where(TemplateDocument.program_id == program_id)
    return (await session.execute(stmt)).scalars().all()


async def get_template(
    session: AsyncSession, template_id: UUID
) -> TemplateDocument | None:
    stmt = (
        select(TemplateDocument)
        .options(selectinload(TemplateDocument.program))
        .where(TemplateDocument.id == template_id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def set_active(
    session: AsyncSession, template_id: UUID
) -> TemplateDocument | None:
    template = await get_template(session, template_id)
    if template is None:
        return None
    # Deactivate other versions for the same program
    await session.execute(
        update(TemplateDocument)
        .where(
            TemplateDocument.program_id == template.program_id,
            TemplateDocument.id != template.id,
        )
        .values(is_active=False)
    )
    template.is_active = True
    await session.commit()
    await session.refresh(template, attribute_names=["program"])
    return template


async def patch_template(
    session: AsyncSession,
    template_id: UUID,
    *,
    title: str | None = None,
    description: str | None = None,
    rubric_json: dict[str, Any] | None = None,
) -> TemplateDocument | None:
    template = await get_template(session, template_id)
    if template is None:
        return None
    if title is not None:
        template.title = title.strip()
    if description is not None:
        template.description = description.strip() or None
    if rubric_json is not None:
        template.rubric_json = rubric_json
    await session.commit()
    await session.refresh(template, attribute_names=["program"])
    return template


async def delete_template(session: AsyncSession, template_id: UUID) -> bool:
    template = await get_template(session, template_id)
    if template is None:
        return False
    storage.delete(template.storage_path)
    await session.delete(template)
    await session.commit()
    return True
