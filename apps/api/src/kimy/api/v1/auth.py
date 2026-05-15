from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import APIRouter, HTTPException, Request, status

from kimy.core.deps import CurrentUser, SessionDep
from kimy.core.rate_limit import LIMIT_LOGIN, LIMIT_REFRESH, LIMIT_REGISTER, limiter
from kimy.core.security import (
    ACCESS_TOKEN_TTL_MIN,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from kimy.schemas.auth import (
    AccessToken,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from kimy.services import users as users_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_pair(user_id: UUID, role: str) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id),
        expires_in=ACCESS_TOKEN_TTL_MIN * 60,
    )


@router.post(
    "/register",
    response_model=TokenPair,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(LIMIT_REGISTER)
async def register(
    request: Request, payload: RegisterRequest, session: SessionDep
) -> TokenPair:
    try:
        user = await users_service.create_user(
            session,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
        )
    except users_service.EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        ) from exc
    return _token_pair(user.id, user.role.value)


@router.post("/login", response_model=TokenPair)
@limiter.limit(LIMIT_LOGIN)
async def login(
    request: Request, payload: LoginRequest, session: SessionDep
) -> TokenPair:
    try:
        user = await users_service.authenticate(
            session, email=payload.email, password=payload.password
        )
    except users_service.InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        ) from exc
    except users_service.InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="user is inactive",
        ) from exc
    return _token_pair(user.id, user.role.value)


@router.post("/refresh", response_model=AccessToken)
@limiter.limit(LIMIT_REFRESH)
async def refresh(
    request: Request, payload: RefreshRequest, session: SessionDep
) -> AccessToken:
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = UUID(decoded["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired refresh token",
        ) from exc

    user = await users_service.get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user not found or inactive",
        )
    return AccessToken(
        access_token=create_access_token(user.id, user.role.value),
        expires_in=ACCESS_TOKEN_TTL_MIN * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
