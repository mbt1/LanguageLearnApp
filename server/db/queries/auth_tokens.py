# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def create_refresh_token(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> dict[str, Any]:
    """Store a hashed refresh token."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
            VALUES (%(user_id)s, %(token_hash)s, %(expires_at)s)
            RETURNING *
            """,
            {"user_id": user_id, "token_hash": token_hash, "expires_at": expires_at},
        )
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_refresh_token(
    conn: AsyncConnection,
    *,
    token_hash: str,
) -> dict[str, Any] | None:
    """Look up a refresh token by hash. Returns None if not found."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM refresh_tokens WHERE token_hash = %(token_hash)s",
            {"token_hash": token_hash},
        )
        return await cur.fetchone()


async def revoke_refresh_token(
    conn: AsyncConnection,
    *,
    token_hash: str,
) -> None:
    """Mark a refresh token as revoked."""
    await conn.execute(
        "UPDATE refresh_tokens SET revoked = true WHERE token_hash = %(token_hash)s",
        {"token_hash": token_hash},
    )


async def revoke_all_user_refresh_tokens(
    conn: AsyncConnection,
    *,
    user_id: UUID,
) -> None:
    """Revoke all refresh tokens for a user (logout-all)."""
    await conn.execute(
        "UPDATE refresh_tokens SET revoked = true WHERE user_id = %(user_id)s",
        {"user_id": user_id},
    )


async def create_email_verification_token(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    token: str,
    expires_at: datetime,
) -> dict[str, Any]:
    """Store an email verification token."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO email_verification_tokens (user_id, token, expires_at)
            VALUES (%(user_id)s, %(token)s, %(expires_at)s)
            RETURNING *
            """,
            {"user_id": user_id, "token": token, "expires_at": expires_at},
        )
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_email_verification_token(
    conn: AsyncConnection,
    *,
    token: str,
) -> dict[str, Any] | None:
    """Look up a verification token. Returns None if not found."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM email_verification_tokens WHERE token = %(token)s",
            {"token": token},
        )
        return await cur.fetchone()


async def delete_email_verification_token(
    conn: AsyncConnection,
    *,
    token: str,
) -> None:
    """Delete a used verification token."""
    await conn.execute(
        "DELETE FROM email_verification_tokens WHERE token = %(token)s",
        {"token": token},
    )


async def mark_user_email_verified(
    conn: AsyncConnection,
    *,
    user_id: UUID,
) -> None:
    """Set email_verified=true for a user."""
    await conn.execute(
        "UPDATE users SET email_verified = true WHERE id = %(user_id)s",
        {"user_id": user_id},
    )
