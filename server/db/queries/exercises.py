# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""Exercise query functions."""

from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def create_exercise(
    conn: AsyncConnection,
    *,
    concept_id: UUID,
    exercise_type: str,
    prompt: str,
    correct_answer: str,
    distractors: list[str] | None = None,
    sentence_template: str | None = None,
) -> dict[str, Any]:
    """Insert a new exercise and return the created row."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO exercises
                (concept_id, exercise_type, prompt, correct_answer, distractors, sentence_template)
            VALUES
                (%(concept_id)s, %(exercise_type)s, %(prompt)s, %(correct_answer)s,
                 %(distractors)s, %(sentence_template)s)
            RETURNING *
            """,
            {
                "concept_id": concept_id,
                "exercise_type": exercise_type,
                "prompt": prompt,
                "correct_answer": correct_answer,
                "distractors": distractors,
                "sentence_template": sentence_template,
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
    """Fetch a random exercise by concept and type, or None if not found."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT * FROM exercises
            WHERE concept_id = %(concept_id)s AND exercise_type = %(exercise_type)s
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
    """Fetch all exercises for a concept, ordered by difficulty."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT * FROM exercises
            WHERE concept_id = %(concept_id)s
            ORDER BY exercise_type
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

    Returns a dict keyed by (concept_id, exercise_type) mapping to a list of
    matching exercises (there may be multiple exercises per type per concept).
    """
    if not items:
        return {}
    concept_ids = list({cid for cid, _ in items})
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT * FROM exercises
            WHERE concept_id = ANY(%(concept_ids)s)
            """,
            {"concept_ids": concept_ids},
        )
        rows = await cur.fetchall()
    result: dict[tuple[UUID, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["concept_id"], row["exercise_type"])
        result.setdefault(key, []).append(row)
    return result
