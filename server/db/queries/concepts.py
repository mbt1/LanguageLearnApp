# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""Concept query functions."""

from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def create_concept(
    conn: AsyncConnection,
    *,
    course_id: UUID,
    concept_type: str,
    cefr_level: str,
    sequence: int,
    prompt: str,
    target: str,
    explanation: str | None = None,
) -> dict[str, Any]:
    """Insert a new concept and return the created row."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO concepts
                (course_id, concept_type, cefr_level, sequence, prompt, target, explanation)
            VALUES
                (%(course_id)s, %(concept_type)s, %(cefr_level)s, %(sequence)s,
                 %(prompt)s, %(target)s, %(explanation)s)
            RETURNING *
            """,
            {
                "course_id": course_id,
                "concept_type": concept_type,
                "cefr_level": cefr_level,
                "sequence": sequence,
                "prompt": prompt,
                "target": target,
                "explanation": explanation,
            },
        )
        row = await cur.fetchone()
    assert row is not None  # noqa: S101
    return row


async def get_concept(conn: AsyncConnection, *, concept_id: UUID) -> dict[str, Any] | None:
    """Fetch a concept by primary key."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM concepts WHERE id = %(concept_id)s",
            {"concept_id": concept_id},
        )
        return await cur.fetchone()


async def list_concepts_by_course(
    conn: AsyncConnection,
    *,
    course_id: UUID,
    cefr_level: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch concepts for a course, optionally filtered by CEFR level."""
    async with conn.cursor(row_factory=dict_row) as cur:
        if cefr_level is not None:
            await cur.execute(
                """
                SELECT * FROM concepts
                WHERE course_id = %(course_id)s AND cefr_level = %(cefr_level)s
                ORDER BY cefr_level, sequence
                """,
                {"course_id": course_id, "cefr_level": cefr_level},
            )
        else:
            await cur.execute(
                """
                SELECT * FROM concepts
                WHERE course_id = %(course_id)s
                ORDER BY cefr_level, sequence
                """,
                {"course_id": course_id},
            )
        return await cur.fetchall()


async def add_prerequisite(
    conn: AsyncConnection,
    *,
    concept_id: UUID,
    prerequisite_id: UUID,
    source: str = "manual",
) -> dict[str, Any]:
    """Add a prerequisite relationship between two concepts."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO concept_prerequisites (concept_id, prerequisite_id, source)
            VALUES (%(concept_id)s, %(prerequisite_id)s, %(source)s)
            RETURNING *
            """,
            {
                "concept_id": concept_id,
                "prerequisite_id": prerequisite_id,
                "source": source,
            },
        )
        row = await cur.fetchone()
    assert row is not None  # noqa: S101
    return row


async def get_prerequisites(
    conn: AsyncConnection,
    *,
    concept_id: UUID,
) -> list[dict[str, Any]]:
    """Fetch all prerequisites for a concept (joined with concept data)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT c.*, cp.source
            FROM concept_prerequisites cp
            JOIN concepts c ON c.id = cp.prerequisite_id
            WHERE cp.concept_id = %(concept_id)s
            ORDER BY c.cefr_level, c.sequence
            """,
            {"concept_id": concept_id},
        )
        return await cur.fetchall()
