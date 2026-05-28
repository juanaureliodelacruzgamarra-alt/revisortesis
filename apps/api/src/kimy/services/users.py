from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kimy.core.security import hash_password, verify_password
from kimy.models.advisor_profile import AdvisorProfile
from kimy.models.student_profile import StudentProfile
from kimy.models.user import User, UserRole


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email.lower())
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def create_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    role: UserRole,
) -> User:
    normalized_email = email.lower().strip()
    if await get_user_by_email(session, normalized_email):
        raise EmailAlreadyExistsError(normalized_email)

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        role=role,
        is_active=True,
    )
    session.add(user)
    await session.flush()

    if role == UserRole.student:
        session.add(StudentProfile(user_id=user.id))
    elif role == UserRole.advisor:
        session.add(AdvisorProfile(user_id=user.id))

    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(
    session: AsyncSession,
    *,
    email: str,
    password: str,
) -> User:
    user = await get_user_by_email(session, email.lower().strip())
    if not user or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError
    if not user.is_active:
        raise InactiveUserError
    return user
