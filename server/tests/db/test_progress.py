# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

import datetime
from typing import Any

import pytest
from psycopg import AsyncConnection

from db.queries.concepts import create_concept
from db.queries.courses import create_course
from db.queries.progress import get_progress, list_due_reviews, upsert_progress
from db.queries.users import create_user


@pytest.fixture
async def user(db_conn: AsyncConnection) -> dict[str, Any]:
    return await create_user(db_conn, email="learner@example.com")


@pytest.fixture
async def course(db_conn: AsyncConnection) -> dict[str, Any]:
    return await create_course(
        db_conn, slug="en-es", title="English to Spanish",
        source_language="en", target_language="es",
    )


@pytest.fixture
async def concept(db_conn: AsyncConnection, course: dict[str, Any]) -> dict[str, Any]:
    return await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )


async def test_upsert_progress_insert(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    progress = await upsert_progress(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    assert progress["current_exercise_difficulty"] == "multiple_choice"
    assert progress["consecutive_correct"] == 0
    assert progress["is_mastered"] is False
    assert progress["fsrs_state"] is None


async def test_upsert_progress_update(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    await upsert_progress(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    now = datetime.datetime.now(tz=datetime.UTC)
    updated = await upsert_progress(
        db_conn,
        user_id=user["id"],
        concept_id=concept["id"],
        current_exercise_difficulty="cloze",
        consecutive_correct=3,
        fsrs_state="learning",
        fsrs_step=1,
        fsrs_stability=2.5,
        fsrs_difficulty=3.0,
        fsrs_due=now + datetime.timedelta(days=1),
        fsrs_last_review=now,
    )
    assert updated["current_exercise_difficulty"] == "cloze"
    assert updated["consecutive_correct"] == 3
    assert updated["fsrs_state"] == "learning"
    assert updated["fsrs_stability"] == pytest.approx(2.5)  # pyright: ignore[reportUnknownMemberType]


async def test_get_progress(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    await upsert_progress(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    progress = await get_progress(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    assert progress is not None
    assert progress["current_exercise_difficulty"] == "multiple_choice"


async def test_get_progress_not_found(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    progress = await get_progress(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    assert progress is None


async def test_list_due_reviews(
    db_conn: AsyncConnection, user: dict, course: dict,
) -> None:
    now = datetime.datetime.now(tz=datetime.UTC)
    # Create two concepts — one due, one not
    c1 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    c2 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="goodbye", target="adiós",
    )
    # c1 is due (past)
    await upsert_progress(
        db_conn, user_id=user["id"], concept_id=c1["id"],
        fsrs_due=now - datetime.timedelta(hours=1),
        fsrs_state="review",
    )
    # c2 is not due (future)
    await upsert_progress(
        db_conn, user_id=user["id"], concept_id=c2["id"],
        fsrs_due=now + datetime.timedelta(days=7),
        fsrs_state="review",
    )

    due = await list_due_reviews(db_conn, user_id=user["id"], now=now)
    assert len(due) == 1
    assert due[0]["concept_id"] == c1["id"]
    assert due[0]["prompt"] == "hello"  # joined from concepts table
