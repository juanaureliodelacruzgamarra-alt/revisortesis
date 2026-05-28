from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.models.academic_program import AcademicProgram, ProgramLevel


class ProgramCodeAlreadyExistsError(Exception):
    pass


async def list_programs(session: AsyncSession) -> list[AcademicProgram]:
    stmt = select(AcademicProgram).order_by(AcademicProgram.name)
    return list((await session.execute(stmt)).scalars().all())


async def get_program(session: AsyncSession, program_id: UUID) -> AcademicProgram | None:
    return await session.get(AcademicProgram, program_id)


async def create_program(
    session: AsyncSession,
    *,
    name: str,
    code: str,
    level: ProgramLevel,
) -> AcademicProgram:
    program = AcademicProgram(name=name.strip(), code=code.strip().upper(), level=level)
    session.add(program)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ProgramCodeAlreadyExistsError(code) from exc
    await session.refresh(program)
    return program


async def delete_program(session: AsyncSession, program_id: UUID) -> bool:
    program = await get_program(session, program_id)
    if program is None:
        return False
    await session.delete(program)
    await session.commit()
    return True
