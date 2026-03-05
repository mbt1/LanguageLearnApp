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
            SELECT ucp.*, c.prompt, c.target, c.concept_type, c.cefr_level, c.explanation
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


async def get_prerequisite_difficulties(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    concept_id: UUID,
) -> list[dict[str, Any]]:
    """Fetch effective exercise difficulties for all prerequisites of a concept.

    Unstarted prerequisites default to 'multiple_choice' via COALESCE.
    """
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                cp.prerequisite_id AS concept_id,
                COALESCE(
                    ucp.current_exercise_difficulty, 'multiple_choice'
                ) AS current_exercise_difficulty
            FROM concept_prerequisites cp
            LEFT JOIN user_concept_progress ucp
                ON ucp.concept_id = cp.prerequisite_id
                AND ucp.user_id = %(user_id)s
            WHERE cp.concept_id = %(concept_id)s
            """,
            {"user_id": user_id, "concept_id": concept_id},
        )
        return await cur.fetchall()


async def get_prerequisite_difficulties_batch(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    concept_ids: list[UUID],
) -> dict[UUID, list[str]]:
    """Batch fetch prerequisite difficulties for multiple concepts.

    Returns a mapping from concept_id to list of prerequisite difficulty strings.
    """
    if not concept_ids:
        return {}
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                cp.concept_id,
                COALESCE(
                    ucp.current_exercise_difficulty, 'multiple_choice'
                ) AS current_exercise_difficulty
            FROM concept_prerequisites cp
            LEFT JOIN user_concept_progress ucp
                ON ucp.concept_id = cp.prerequisite_id
                AND ucp.user_id = %(user_id)s
            WHERE cp.concept_id = ANY(%(concept_ids)s)
            """,
            {"user_id": user_id, "concept_ids": concept_ids},
        )
        rows = await cur.fetchall()

    result: dict[UUID, list[str]] = {}
    for row in rows:
        cid = row["concept_id"]
        result.setdefault(cid, []).append(row["current_exercise_difficulty"])
    return result


async def list_new_concepts(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    course_id: UUID,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Fetch concepts the user has not yet started, ordered by cefr_level + sequence."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT c.*
            FROM concepts c
            LEFT JOIN user_concept_progress ucp
                ON ucp.concept_id = c.id AND ucp.user_id = %(user_id)s
            WHERE c.course_id = %(course_id)s
              AND ucp.concept_id IS NULL
            ORDER BY c.cefr_level, c.sequence
            LIMIT %(limit)s
            """,
            {"user_id": user_id, "course_id": course_id, "limit": limit},
        )
        return await cur.fetchall()


async def list_all_progress_detail(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    course_id: UUID,
) -> list[dict[str, Any]]:
    """Fetch all progress rows for a user in a course, joined with concept data."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                ucp.concept_id,
                ucp.current_exercise_difficulty,
                ucp.consecutive_correct,
                ucp.fsrs_state,
                ucp.fsrs_stability,
                ucp.fsrs_difficulty,
                ucp.fsrs_due,
                ucp.fsrs_last_review,
                ucp.is_mastered,
                c.prompt,
                c.target,
                c.concept_type,
                c.cefr_level,
                c.sequence
            FROM user_concept_progress ucp
            JOIN concepts c ON c.id = ucp.concept_id
            WHERE ucp.user_id = %(user_id)s
              AND c.course_id = %(course_id)s
            ORDER BY c.cefr_level, c.sequence
            """,
            {"user_id": user_id, "course_id": course_id},
        )
        return await cur.fetchall()


async def list_all_active_progress(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    course_id: UUID,
) -> list[dict[str, Any]]:
    """Fetch all progress rows with a scheduled due date (for throttling calculation)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT ucp.*
            FROM user_concept_progress ucp
            JOIN concepts c ON c.id = ucp.concept_id
            WHERE ucp.user_id = %(user_id)s
              AND c.course_id = %(course_id)s
              AND ucp.fsrs_due IS NOT NULL
            """,
            {"user_id": user_id, "course_id": course_id},
        )
        return await cur.fetchall()


async def get_progress_summary(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    course_id: UUID,
) -> list[dict[str, Any]]:
    """Return stage counts per CEFR level for a user in a course.

    Stages map to exercise difficulty progression:
      not_started, seen (MC), familiar (cloze), practiced (rev_typing),
      proficient (typing, not mastered), mastered.
    """
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                c.cefr_level,
                COUNT(*) AS total_concepts,
                COUNT(*) - COUNT(ucp.concept_id) AS not_started,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'multiple_choice'
                      AND NOT ucp.is_mastered
                ) AS seen,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'cloze'
                      AND NOT ucp.is_mastered
                ) AS familiar,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'reverse_typing'
                      AND NOT ucp.is_mastered
                ) AS practiced,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'typing'
                      AND NOT ucp.is_mastered
                ) AS proficient,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.is_mastered = true
                ) AS mastered
            FROM concepts c
            LEFT JOIN user_concept_progress ucp
                ON ucp.concept_id = c.id AND ucp.user_id = %(user_id)s
            WHERE c.course_id = %(course_id)s
            GROUP BY c.cefr_level
            ORDER BY c.cefr_level
            """,
            {"user_id": user_id, "course_id": course_id},
        )
        return await cur.fetchall()


async def get_all_progress_summary(
    conn: AsyncConnection,
    *,
    user_id: UUID,
) -> list[dict[str, Any]]:
    """Return stage counts per course + CEFR level for a user (single query)."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                c.course_id,
                c.cefr_level,
                COUNT(*) AS total_concepts,
                COUNT(*) - COUNT(ucp.concept_id) AS not_started,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'multiple_choice'
                      AND NOT ucp.is_mastered
                ) AS seen,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'cloze'
                      AND NOT ucp.is_mastered
                ) AS familiar,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'reverse_typing'
                      AND NOT ucp.is_mastered
                ) AS practiced,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'typing'
                      AND NOT ucp.is_mastered
                ) AS proficient,
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.is_mastered = true
                ) AS mastered
            FROM concepts c
            LEFT JOIN user_concept_progress ucp
                ON ucp.concept_id = c.id AND ucp.user_id = %(user_id)s
            GROUP BY c.course_id, c.cefr_level
            ORDER BY c.course_id, c.cefr_level
            """,
            {"user_id": user_id},
        )
        return await cur.fetchall()


# ── Precalculated progress cache ─────────────────────────


async def refresh_progress_summary(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    course_id: UUID,
    cefr_level: str,
) -> None:
    """Recompute and upsert one row in user_progress_summary."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO user_progress_summary
                (user_id, course_id, cefr_level,
                 total_concepts, not_started, seen, familiar,
                 practiced, proficient, mastered, updated_at)
            SELECT
                %(user_id)s,
                %(course_id)s,
                c.cefr_level,
                COUNT(*),
                COUNT(*) - COUNT(ucp.concept_id),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'multiple_choice'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'cloze'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'reverse_typing'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'typing'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.is_mastered = true),
                now()
            FROM concepts c
            LEFT JOIN user_concept_progress ucp
                ON ucp.concept_id = c.id AND ucp.user_id = %(user_id)s
            WHERE c.course_id = %(course_id)s AND c.cefr_level = %(cefr_level)s
            GROUP BY c.cefr_level
            ON CONFLICT (user_id, course_id, cefr_level) DO UPDATE SET
                total_concepts = EXCLUDED.total_concepts,
                not_started    = EXCLUDED.not_started,
                seen           = EXCLUDED.seen,
                familiar       = EXCLUDED.familiar,
                practiced      = EXCLUDED.practiced,
                proficient     = EXCLUDED.proficient,
                mastered       = EXCLUDED.mastered,
                updated_at     = EXCLUDED.updated_at
            """,
            {"user_id": user_id, "course_id": course_id, "cefr_level": cefr_level},
        )


async def refresh_course_progress_summary(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    course_id: UUID,
) -> None:
    """Recompute all CEFR level rows for a user+course in user_progress_summary."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO user_progress_summary
                (user_id, course_id, cefr_level,
                 total_concepts, not_started, seen, familiar,
                 practiced, proficient, mastered, updated_at)
            SELECT
                %(user_id)s,
                %(course_id)s,
                c.cefr_level,
                COUNT(*),
                COUNT(*) - COUNT(ucp.concept_id),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'multiple_choice'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'cloze'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'reverse_typing'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.current_exercise_difficulty = 'typing'
                      AND NOT ucp.is_mastered),
                COUNT(ucp.concept_id) FILTER (
                    WHERE ucp.is_mastered = true),
                now()
            FROM concepts c
            LEFT JOIN user_concept_progress ucp
                ON ucp.concept_id = c.id AND ucp.user_id = %(user_id)s
            WHERE c.course_id = %(course_id)s
            GROUP BY c.cefr_level
            ON CONFLICT (user_id, course_id, cefr_level) DO UPDATE SET
                total_concepts = EXCLUDED.total_concepts,
                not_started    = EXCLUDED.not_started,
                seen           = EXCLUDED.seen,
                familiar       = EXCLUDED.familiar,
                practiced      = EXCLUDED.practiced,
                proficient     = EXCLUDED.proficient,
                mastered       = EXCLUDED.mastered,
                updated_at     = EXCLUDED.updated_at
            """,
            {"user_id": user_id, "course_id": course_id},
        )


async def read_progress_summary(
    conn: AsyncConnection,
    *,
    user_id: UUID,
    course_id: UUID,
) -> list[dict[str, Any]]:
    """Read cached progress summary for a course. Falls back to empty list."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT cefr_level, total_concepts, not_started,
                   seen, familiar, practiced, proficient, mastered
            FROM user_progress_summary
            WHERE user_id = %(user_id)s AND course_id = %(course_id)s
            ORDER BY cefr_level
            """,
            {"user_id": user_id, "course_id": course_id},
        )
        return await cur.fetchall()


async def read_all_progress_summary(
    conn: AsyncConnection,
    *,
    user_id: UUID,
) -> list[dict[str, Any]]:
    """Read cached progress summary for all courses."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT course_id, cefr_level, total_concepts, not_started,
                   seen, familiar, practiced, proficient, mastered
            FROM user_progress_summary
            WHERE user_id = %(user_id)s
            ORDER BY course_id, cefr_level
            """,
            {"user_id": user_id},
        )
        return await cur.fetchall()
