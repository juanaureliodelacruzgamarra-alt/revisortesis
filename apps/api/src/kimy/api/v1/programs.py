from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from kimy.core.deps import SessionDep, require_roles
from kimy.models.user import UserRole
from kimy.schemas.programs import ProgramCreate, ProgramOut
from kimy.services import programs as programs_service

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[ProgramOut])
async def list_programs(session: SessionDep) -> list[ProgramOut]:
    items = await programs_service.list_programs(session)
    return [ProgramOut.model_validate(p) for p in items]


@router.post(
    "",
    response_model=ProgramOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles(UserRole.admin, UserRole.coordinator))],
)
async def create_program(
    payload: ProgramCreate, session: SessionDep
) -> ProgramOut:
    try:
        program = await programs_service.create_program(
            session, name=payload.name, code=payload.code, level=payload.level
        )
    except programs_service.ProgramCodeAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="program code already exists",
        ) from exc
    return ProgramOut.model_validate(program)


@router.delete(
    "/{program_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_roles(UserRole.admin))],
)
async def delete_program(program_id: UUID, session: SessionDep) -> None:
    deleted = await programs_service.delete_program(session, program_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="program not found"
        )
