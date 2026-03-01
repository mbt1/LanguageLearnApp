# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from psycopg import AsyncConnection
from psycopg.errors import UniqueViolation

from auth.config import get_config
from auth.dependencies import get_current_user
from auth.email import get_email_provider
from auth.passwords import hash_password, verify_password
from auth.schemas import (
    CurrentUser,
    LoginRequest,
    LoginResponse,
    RefreshResponse,
    RegisterRequest,
    RegisterResponse,
    VerifyEmailResponse,
)
from auth.tokens import (
    create_access_token,
    generate_email_verification_token,
    generate_refresh_token,
    hash_refresh_token,
)
from db.pool import get_conn
from db.queries.auth_tokens import (
    create_email_verification_token,
    create_refresh_token,
    delete_email_verification_token,
    get_email_verification_token,
    get_refresh_token,
    mark_user_email_verified,
    revoke_refresh_token,
)
from db.queries.users import create_user, get_user_by_email, get_user_by_id

router = APIRouter(prefix="/v1/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
# Dummy password hash for constant-time login (computed once at import)
_DUMMY_HASH = hash_password("dummy-constant-time-defense")


def _set_refresh_cookie(response: Response, token: str, max_age: int) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/v1/auth",
        max_age=max_age,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/v1/auth")


async def _issue_tokens(
    conn: AsyncConnection,
    response: Response,
    *,
    user_id: str,
    email: str,
    email_verified: bool,
) -> str:
    """Create access + refresh tokens, store refresh hash, set cookie. Returns access token."""
    config = get_config()
    access_token = create_access_token(
        user_id=UUID(user_id),
        email=email,
        email_verified=email_verified,
        secret=config.jwt_secret,
        algorithm=config.jwt_algorithm,
        expires_minutes=config.access_token_expire_minutes,
    )
    refresh_tok = generate_refresh_token()
    expires_at = datetime.now(UTC) + timedelta(days=config.refresh_token_expire_days)
    await create_refresh_token(
        conn,
        user_id=UUID(user_id),
        token_hash=hash_refresh_token(refresh_tok),
        expires_at=expires_at,
    )
    _set_refresh_cookie(
        response,
        refresh_tok,
        max_age=config.refresh_token_expire_days * 86400,
    )
    return access_token


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> RegisterResponse:
    """Register a new user with email and password."""
    pw_hash = hash_password(body.password)
    try:
        user = await create_user(
            conn,
            email=body.email,
            display_name=body.display_name,
            password_hash=pw_hash,
        )
    except UniqueViolation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None

    # Email verification
    config = get_config()
    ev_token = generate_email_verification_token()
    ev_expires = datetime.now(UTC) + timedelta(
        hours=config.email_verification_expire_hours
    )
    await create_email_verification_token(
        conn, user_id=user["id"], token=ev_token, expires_at=ev_expires
    )
    verification_url = f"{config.rp_origin}/verify-email?token={ev_token}"
    provider = get_email_provider()
    await provider.send_verification_email(body.email, verification_url)

    access_token = await _issue_tokens(
        conn,
        response,
        user_id=str(user["id"]),
        email=user["email"],
        email_verified=False,
    )
    await conn.commit()
    return RegisterResponse(
        user_id=user["id"],
        email=user["email"],
        access_token=access_token,
        message="Verification email sent",
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    response: Response,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> LoginResponse:
    """Login with email and password."""
    user = await get_user_by_email(conn, email=body.email)
    if user is None:
        # Constant-time: still hash to prevent timing leaks
        verify_password(body.password, _DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user["password_hash"] is None:
        # Passkey-only user, no password set
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = await _issue_tokens(
        conn,
        response,
        user_id=str(user["id"]),
        email=user["email"],
        email_verified=user["email_verified"],
    )
    await conn.commit()
    return LoginResponse(
        user_id=user["id"],
        email=user["email"],
        email_verified=user["email_verified"],
        access_token=access_token,
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    request: Request,
    response: Response,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> RefreshResponse:
    """Refresh access token using refresh token cookie."""
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if raw_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    token_hash = hash_refresh_token(raw_token)
    stored = await get_refresh_token(conn, token_hash=token_hash)
    if stored is None or stored["revoked"]:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    if stored["expires_at"].replace(tzinfo=UTC) < datetime.now(UTC):
        await revoke_refresh_token(conn, token_hash=token_hash)
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Rotate: revoke old, issue new
    await revoke_refresh_token(conn, token_hash=token_hash)

    user = await get_user_by_id(conn, user_id=stored["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access_token = await _issue_tokens(
        conn,
        response,
        user_id=str(user["id"]),
        email=user["email"],
        email_verified=user["email_verified"],
    )
    await conn.commit()
    return RefreshResponse(access_token=access_token)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> None:
    """Logout: revoke refresh token and clear cookie."""
    raw_token = request.cookies.get(_REFRESH_COOKIE)
    if raw_token:
        token_hash = hash_refresh_token(raw_token)
        await revoke_refresh_token(conn, token_hash=token_hash)
        await conn.commit()
    _clear_refresh_cookie(response)


@router.get("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    token: str,
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> VerifyEmailResponse:
    """Verify email address using token from verification link."""
    stored = await get_email_verification_token(conn, token=token)
    if stored is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid verification token",
        )
    if stored["expires_at"].replace(tzinfo=UTC) < datetime.now(UTC):
        await delete_email_verification_token(conn, token=token)
        await conn.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token expired",
        )

    await mark_user_email_verified(conn, user_id=stored["user_id"])
    await delete_email_verification_token(conn, token=token)
    await conn.commit()
    return VerifyEmailResponse(message="Email verified successfully")


@router.post("/resend-verification", status_code=204)
async def resend_verification(
    conn: Annotated[AsyncConnection, Depends(get_conn)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> None:
    """Resend email verification link."""
    if current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified",
        )
    config = get_config()
    ev_token = generate_email_verification_token()
    ev_expires = datetime.now(UTC) + timedelta(
        hours=config.email_verification_expire_hours
    )
    await create_email_verification_token(
        conn, user_id=current_user.user_id, token=ev_token, expires_at=ev_expires
    )
    verification_url = f"{config.rp_origin}/verify-email?token={ev_token}"
    provider = get_email_provider()
    await provider.send_verification_email(current_user.email, verification_url)
    await conn.commit()
