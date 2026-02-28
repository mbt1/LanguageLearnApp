# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""Course query functions."""

from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def create_course(
    conn: AsyncConnection,
    *,
    slug: str,
    title: str,
    source_language: str,
    target_language: str,
) -> dict[str, Any]:
    """Insert a new course and return the created row."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO courses (slug, title, source_language, target_language)
            VALUES (%(slug)s, %(title)s, %(source_language)s, %(target_language)s)
            RETURNING *
            """,
            {
                "slug": slug,
                "title": title,
                "source_language": source_language,
                "target_language": target_language,
            },
        )
        row = await cur.fetchone()
    assert row is not None  # noqa: S101
    return row


async def get_course(conn: AsyncConnection, *, course_id: UUID) -> dict[str, Any] | None:
    """Fetch a course by primary key."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM courses WHERE id = %(course_id)s",
            {"course_id": course_id},
        )
        return await cur.fetchone()


async def list_courses(conn: AsyncConnection) -> list[dict[str, Any]]:
    """Fetch all courses ordered by title."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM courses ORDER BY title")
        return await cur.fetchall()
