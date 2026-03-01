# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from auth.dependencies import get_current_user, require_verified_email
from auth.schemas import CurrentUser
from auth.tokens import create_access_token

SECRET = "dev-secret-change-me"


async def test_get_current_user_with_valid_token() -> None:
    user_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        email="alice@test.com",
        email_verified=True,
        secret=SECRET,
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    user = await get_current_user(creds)
    assert user.user_id == user_id
    assert user.email == "alice@test.com"
    assert user.email_verified is True


async def test_get_current_user_missing_header() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)
    assert exc_info.value.status_code == 401


async def test_get_current_user_expired_token() -> None:
    token = create_access_token(
        user_id=uuid4(),
        email="bob@test.com",
        email_verified=False,
        secret=SECRET,
        expires_minutes=-1,
    )
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(creds)
    assert exc_info.value.status_code == 401


async def test_get_current_user_malformed_token() -> None:
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="garbage.token.here")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(creds)
    assert exc_info.value.status_code == 401


async def test_require_verified_email_verified_user() -> None:
    user = CurrentUser(user_id=uuid4(), email="a@b.com", email_verified=True)
    result = await require_verified_email(user)
    assert result.email_verified is True


async def test_require_verified_email_unverified_user() -> None:
    user = CurrentUser(user_id=uuid4(), email="a@b.com", email_verified=False)
    with pytest.raises(HTTPException) as exc_info:
        await require_verified_email(user)
    assert exc_info.value.status_code == 403
