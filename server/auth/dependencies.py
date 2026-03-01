# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.config import get_config
from auth.schemas import CurrentUser
from auth.tokens import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> CurrentUser:
    """Extract and validate the access token from the Authorization header."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    config = get_config()
    try:
        payload = decode_access_token(
            credentials.credentials,
            secret=config.jwt_secret,
            algorithm=config.jwt_algorithm,
        )
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None
    return CurrentUser(
        user_id=UUID(payload["sub"]),
        email=payload["email"],
        email_verified=payload["email_verified"],
    )


async def require_verified_email(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Same as get_current_user but also requires email_verified=True."""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return current_user
