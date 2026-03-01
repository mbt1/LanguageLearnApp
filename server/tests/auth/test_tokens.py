# SPDX-License-Identifier: Apache-2.0
from uuid import uuid4

import jwt
import pytest

from auth.tokens import (
    create_access_token,
    decode_access_token,
    generate_email_verification_token,
    generate_refresh_token,
    hash_refresh_token,
)

SECRET = "test-secret"


def test_create_and_decode_access_token() -> None:
    user_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        email="test@example.com",
        email_verified=False,
        secret=SECRET,
    )
    payload = decode_access_token(token, secret=SECRET)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "test@example.com"
    assert payload["email_verified"] is False


def test_decode_expired_token_raises() -> None:
    token = create_access_token(
        user_id=uuid4(),
        email="test@example.com",
        email_verified=False,
        secret=SECRET,
        expires_minutes=-1,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token, secret=SECRET)


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-real-token", secret=SECRET)


def test_token_contains_expected_claims() -> None:
    user_id = uuid4()
    token = create_access_token(
        user_id=user_id,
        email="alice@example.com",
        email_verified=True,
        secret=SECRET,
    )
    payload = decode_access_token(token, secret=SECRET)
    assert "sub" in payload
    assert "email" in payload
    assert "email_verified" in payload
    assert "exp" in payload
    assert "iat" in payload
    assert payload["email_verified"] is True


def test_generate_refresh_token_is_unique() -> None:
    t1 = generate_refresh_token()
    t2 = generate_refresh_token()
    assert t1 != t2
    assert len(t1) > 30  # URL-safe base64 of 48 bytes


def test_hash_refresh_token_deterministic() -> None:
    token = generate_refresh_token()
    h1 = hash_refresh_token(token)
    h2 = hash_refresh_token(token)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex digest


def test_generate_email_verification_token() -> None:
    t1 = generate_email_verification_token()
    t2 = generate_email_verification_token()
    assert t1 != t2
    assert len(t1) > 20
