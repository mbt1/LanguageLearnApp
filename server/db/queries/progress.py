# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""User concept progress query functions."""

import datetime
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row


async def get_progress(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    concept_id: UUID,
) -> dict[str, Any] | None:
    """Fetch progress for a specific user + concept pair."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT * FROM user_concept_progress
            WHERE user_id = %(user_id)s AND concept_id = %(concept_id)s
            """,
            {"user_id": user_id, "concept_id": concept_id},
        )
        return await cur.fetchone()


async def upsert_progress(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    concept_id: UUID,
    current_exercise_difficulty: str = "multiple_choice",
    consecutive_correct: int = 0,
    fsrs_state: str | None = None,
    fsrs_step: int | None = None,
    fsrs_stability: float | None = None,
    fsrs_difficulty: float | None = None,
    fsrs_due: datetime.datetime | None = None,
    fsrs_last_review: datetime.datetime | None = None,
    is_mastered: bool = False,
) -> dict[str, Any]:
    """Insert or update progress for a user + concept pair."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO user_concept_progress (
                user_id, concept_id, current_exercise_difficulty, consecutive_correct,
                fsrs_state, fsrs_step, fsrs_stability, fsrs_difficulty,
                fsrs_due, fsrs_last_review, is_mastered
            ) VALUES (
                %(user_id)s, %(concept_id)s, %(current_exercise_difficulty)s,
                %(consecutive_correct)s, %(fsrs_state)s, %(fsrs_step)s,
                %(fsrs_stability)s, %(fsrs_difficulty)s, %(fsrs_due)s,
                %(fsrs_last_review)s, %(is_mastered)s
            )
            ON CONFLICT (user_id, concept_id) DO UPDATE SET
                current_exercise_difficulty = EXCLUDED.current_exercise_difficulty,
                consecutive_correct = EXCLUDED.consecutive_correct,
                fsrs_state = EXCLUDED.fsrs_state,
                fsrs_step = EXCLUDED.fsrs_step,
                fsrs_stability = EXCLUDED.fsrs_stability,
                fsrs_difficulty = EXCLUDED.fsrs_difficulty,
                fsrs_due = EXCLUDED.fsrs_due,
                fsrs_last_review = EXCLUDED.fsrs_last_review,
                is_mastered = EXCLUDED.is_mastered
            RETURNING *
            """,
            {
                "user_id": user_id,
                "concept_id": concept_id,
                "current_exercise_difficulty": current_exercise_difficulty,
                "consecutive_correct": consecutive_correct,
                "fsrs_state": fsrs_state,
                "fsrs_step": fsrs_step,
                "fsrs_stability": fsrs_stability,
                "fsrs_difficulty": fsrs_difficulty,
                "fsrs_due": fsrs_due,
                "fsrs_last_review": fsrs_last_review,
                "is_mastered": is_mastered,
            },
        )
        row = await cur.fetchone()
    assert row is not None
    return row


async def list_due_reviews(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    now: datetime.datetime,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Fetch concepts due for review, ordered by earliest due date."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT ucp.*, c.prompt, c.target, c.concept_type, c.cefr_level
            FROM user_concept_progress ucp
            JOIN concepts c ON c.id = ucp.concept_id
            WHERE ucp.user_id = %(user_id)s
              AND ucp.fsrs_due IS NOT NULL
              AND ucp.fsrs_due <= %(now)s
            ORDER BY ucp.fsrs_due
            LIMIT %(limit)s
            """,
            {"user_id": user_id, "now": now, "limit": limit},
        )
        return await cur.fetchall()
