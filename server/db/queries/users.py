# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""User query functions."""

from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def create_user(
    conn: AsyncConnection,
    *,
    email: str,
    display_name: str | None = None,
    password_hash: str | None = None,
) -> dict[str, Any]:
    """Insert a new user and return the created row."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO users (email, display_name, password_hash)
            VALUES (%(email)s, %(display_name)s, %(password_hash)s)
            RETURNING *
            """,
            {"email": email, "display_name": display_name, "password_hash": password_hash},
        )
        row = await cur.fetchone()
    assert row is not None  # noqa: S101
    return row


async def get_user_by_id(conn: AsyncConnection, *, user_id: UUID) -> dict[str, Any] | None:
    """Fetch a user by primary key."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM users WHERE id = %(user_id)s", {"user_id": user_id})
        return await cur.fetchone()


async def get_user_by_email(conn: AsyncConnection, *, email: str) -> dict[str, Any] | None:
    """Fetch a user by email address."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM users WHERE email = %(email)s", {"email": email})
        return await cur.fetchone()
