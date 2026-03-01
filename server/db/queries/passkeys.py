# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def create_passkey(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    credential_id: bytes,
    public_key: bytes,
    sign_count: int,
    name: str | None = None,
) -> dict[str, Any]:
    """Store a new passkey credential."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO user_passkeys (user_id, credential_id, public_key, sign_count, name)
            VALUES (%(user_id)s, %(credential_id)s, %(public_key)s, %(sign_count)s, %(name)s)
            RETURNING *
            """,
            {
                "user_id": user_id,
                "credential_id": credential_id,
                "public_key": public_key,
                "sign_count": sign_count,
                "name": name,
            },
        )
        row = await cur.fetchone()
        assert row is not None
        return row


async def get_passkey_by_credential_id(
    conn: AsyncConnection,
    *,
    credential_id: bytes,
) -> dict[str, Any] | None:
    """Look up a passkey by credential_id."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM user_passkeys WHERE credential_id = %(credential_id)s",
            {"credential_id": credential_id},
        )
        return await cur.fetchone()


async def list_passkeys_for_user(
    conn: AsyncConnection,
    *,
    user_id: UUID,
) -> list[dict[str, Any]]:
    """List all passkeys for a user."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM user_passkeys WHERE user_id = %(user_id)s ORDER BY created_at",
            {"user_id": user_id},
        )
        return await cur.fetchall()


async def update_passkey_sign_count(
    conn: AsyncConnection,
    *,
    credential_id: bytes,
    sign_count: int,
) -> None:
    """Update sign count after successful authentication."""
    await conn.execute(
        """
        UPDATE user_passkeys SET sign_count = %(sign_count)s
        WHERE credential_id = %(credential_id)s
        """,
        {"credential_id": credential_id, "sign_count": sign_count},
    )


async def delete_passkey(
    conn: AsyncConnection,
    *,
    passkey_id: UUID,
    user_id: UUID,
) -> bool:
    """Delete a passkey (must belong to user). Returns True if deleted."""
    result = await conn.execute(
        "DELETE FROM user_passkeys WHERE id = %(id)s AND user_id = %(user_id)s",
        {"id": passkey_id, "user_id": user_id},
    )
    return result.rowcount > 0
