# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt


def create_access_token(
    *,
    user_id: UUID,
    email: str,
    email_verified: bool,
    secret: str,
    algorithm: str = "HS256",
    expires_minutes: int = 15,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "email_verified": email_verified,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(
    token: str,
    *,
    secret: str,
    algorithm: str = "HS256",
) -> dict[str, Any]:
    """Decode and validate a JWT access token. Raises jwt.InvalidTokenError on failure."""
    payload: dict[str, Any] = jwt.decode(token, secret, algorithms=[algorithm])
    return payload


def generate_refresh_token() -> str:
    """Generate a cryptographically random refresh token (URL-safe, 48 bytes)."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hash a refresh token for database storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_email_verification_token() -> str:
    """Generate a URL-safe token for email verification."""
    return secrets.token_urlsafe(32)
