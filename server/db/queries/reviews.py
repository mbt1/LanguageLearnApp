# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""Review history query functions."""

from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def record_review(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    concept_id: UUID,
    exercise_type: str,
    rating: str,
    correct: bool,
    response: str | None = None,
    review_duration_ms: int | None = None,
) -> dict[str, Any]:
    """Record a single review attempt."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO review_history
                (user_id, concept_id, exercise_type, rating, response, correct, review_duration_ms)
            VALUES
                (%(user_id)s, %(concept_id)s, %(exercise_type)s, %(rating)s,
                 %(response)s, %(correct)s, %(review_duration_ms)s)
            RETURNING *
            """,
            {
                "user_id": user_id,
                "concept_id": concept_id,
                "exercise_type": exercise_type,
                "rating": rating,
                "response": response,
                "correct": correct,
                "review_duration_ms": review_duration_ms,
            },
        )
        row = await cur.fetchone()
    assert row is not None
    return row


async def get_review_history(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    concept_id: UUID,
) -> list[dict[str, Any]]:
    """Fetch review history for a user + concept, most recent first."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT * FROM review_history
            WHERE user_id = %(user_id)s AND concept_id = %(concept_id)s
            ORDER BY reviewed_at DESC
            """,
            {"user_id": user_id, "concept_id": concept_id},
        )
        return await cur.fetchall()
