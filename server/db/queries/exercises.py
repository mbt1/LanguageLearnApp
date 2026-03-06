# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""Exercise query functions."""

import json
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def create_exercise(
    conn: AsyncConnection,
    *,
    exercise_type: str,
    ref: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Insert a new exercise and return the created row."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO exercises (exercise_type, ref, data)
            VALUES (%(exercise_type)s, %(ref)s, %(data)s)
            RETURNING *
            """,
            {
                "exercise_type": exercise_type,
                "ref": ref,
                "data": json.dumps(data or {}),
            },
        )
        row = await cur.fetchone()
    assert row is not None
    return row


async def create_exercise_concept(
    conn: AsyncConnection,
    *,
    exercise_id: UUID,
    concept_id: UUID,
    is_primary: bool = True,
) -> dict[str, Any]:
    """Link an exercise to a concept via the junction table."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO exercise_concepts (exercise_id, concept_id, is_primary)
            VALUES (%(exercise_id)s, %(concept_id)s, %(is_primary)s)
            RETURNING *
            """,
            {
                "exercise_id": exercise_id,
                "concept_id": concept_id,
                "is_primary": is_primary,
            },
        )
        row = await cur.fetchone()
    assert row is not None
    return row


async def get_exercise_by_type(
    conn: AsyncConnection,
    *,
    concept_id: UUID,
    exercise_type: str,
) -> dict[str, Any] | None:
    """Fetch a random exercise by concept and type via junction table."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT e.* FROM exercises e
            JOIN exercise_concepts ec ON ec.exercise_id = e.id
            WHERE ec.concept_id = %(concept_id)s AND e.exercise_type = %(exercise_type)s
            ORDER BY random()
            LIMIT 1
            """,
            {"concept_id": concept_id, "exercise_type": exercise_type},
        )
        return await cur.fetchone()


async def get_exercise_by_id(
    conn: AsyncConnection,
    *,
    exercise_id: UUID,
) -> dict[str, Any] | None:
    """Fetch a single exercise by primary key."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM exercises WHERE id = %(exercise_id)s",
            {"exercise_id": exercise_id},
        )
        return await cur.fetchone()


async def get_exercises_for_concept(
    conn: AsyncConnection,
    *,
    concept_id: UUID,
) -> list[dict[str, Any]]:
    """Fetch all exercises for a concept via junction table."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT e.* FROM exercises e
            JOIN exercise_concepts ec ON ec.exercise_id = e.id
            WHERE ec.concept_id = %(concept_id)s
            ORDER BY e.exercise_type
            """,
            {"concept_id": concept_id},
        )
        return await cur.fetchall()


async def get_exercises_for_session(
    conn: AsyncConnection,
    *,
    items: list[tuple[UUID, str]],
) -> dict[tuple[UUID, str], list[dict[str, Any]]]:
    """Batch fetch exercises matching (concept_id, exercise_type) pairs.

    Uses junction table. Returns a dict keyed by (concept_id, exercise_type).
    """
    if not items:
        return {}
    concept_ids = list({cid for cid, _ in items})
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT e.*, ec.concept_id FROM exercises e
            JOIN exercise_concepts ec ON ec.exercise_id = e.id
            WHERE ec.concept_id = ANY(%(concept_ids)s)
            """,
            {"concept_ids": concept_ids},
        )
        rows = await cur.fetchall()
    result: dict[tuple[UUID, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["concept_id"], row["exercise_type"])
        result.setdefault(key, []).append(row)
    return result
