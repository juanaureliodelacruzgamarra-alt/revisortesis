from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse

from kimy.core.deps import CurrentUser, SessionDep, require_roles
from kimy.models.user import UserRole
from kimy.schemas.templates import TemplateDetail, TemplatePatch, TemplateSummary
from kimy.services import programs as programs_service
from kimy.services import storage
from kimy.services import templates as templates_service

router = APIRouter(prefix="/templates", tags=["templates"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

_CoordOrAdmin = require_roles(UserRole.coordinator, UserRole.admin)


@router.get("", response_model=list[TemplateSummary])
async def list_templates(
    session: SessionDep,
    program_id: Annotated[UUID | None, Query()] = None,
) -> list[TemplateSummary]:
    items = await templates_service.list_templates(session, program_id=program_id)
    return [TemplateSummary.model_validate(t) for t in items]


@router.post(
    "",
    response_model=TemplateDetail,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_CoordOrAdmin)],
)
async def upload_template(
    session: SessionDep,
    user: CurrentUser,
    program_id: Annotated[UUID, Form()],
    title: Annotated[str, Form(min_length=2, max_length=255)],
    description: Annotated[str | None, Form(max_length=2000)] = None,
    file: UploadFile = File(...),
) -> TemplateDetail:
    program = await programs_service.get_program(session, program_id)
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="program not found"
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"file exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit",
        )

    try:
        template = await templates_service.upload_template(
            session,
            program_id=program_id,
            title=title,
            description=description,
            filename=file.filename or "upload.bin",
            content=content,
            mime_type=file.content_type or "application/octet-stream",
            created_by=user.id,
        )
    except templates_service.UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc

    return TemplateDetail.model_validate(template)


@router.get("/{template_id}", response_model=TemplateDetail)
async def get_template(
    template_id: UUID, session: SessionDep
) -> TemplateDetail:
    template = await templates_service.get_template(session, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="template not found"
        )
    return TemplateDetail.model_validate(template)


@router.patch(
    "/{template_id}",
    response_model=TemplateDetail,
    dependencies=[Depends(_CoordOrAdmin)],
)
async def patch_template(
    template_id: UUID,
    payload: TemplatePatch,
    session: SessionDep,
) -> TemplateDetail:
    template = await templates_service.patch_template(
        session,
        template_id,
        title=payload.title,
        description=payload.description,
        rubric_json=payload.rubric_json,
    )
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="template not found"
        )
    return TemplateDetail.model_validate(template)


@router.post(
    "/{template_id}/activate",
    response_model=TemplateDetail,
    dependencies=[Depends(_CoordOrAdmin)],
)
async def activate_template(
    template_id: UUID, session: SessionDep
) -> TemplateDetail:
    template = await templates_service.set_active(session, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="template not found"
        )
    return TemplateDetail.model_validate(template)


@router.get("/{template_id}/file")
async def download_template(
    template_id: UUID, session: SessionDep, _: CurrentUser
) -> FileResponse:
    template = await templates_service.get_template(session, template_id)
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="template not found"
        )
    path = storage.resolve(template.storage_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="file missing on disk"
        )
    return FileResponse(
        path=path,
        filename=template.original_filename,
        media_type=template.mime_type,
    )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_CoordOrAdmin)],
)
async def delete_template(template_id: UUID, session: SessionDep) -> None:
    deleted = await templates_service.delete_template(session, template_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="template not found"
        )
