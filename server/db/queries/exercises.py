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
