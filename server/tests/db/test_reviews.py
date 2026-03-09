# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from typing import Any

import pytest
from psycopg import AsyncConnection

from db.queries.concepts import create_concept
from db.queries.courses import create_course
from db.queries.reviews import get_review_history, record_review
from db.queries.users import create_user


@pytest.fixture
async def user(db_conn: AsyncConnection) -> dict[str, Any]:
    return await create_user(db_conn, email="reviewer@example.com")


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
        cefr_level="A1", sequence=1, ref="hello",
    )


async def test_record_review(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    review = await record_review(
        db_conn,
        user_id=user["id"],
        concept_id=concept["id"],
        exercise_type="forward_mc",
        rating="good",
        correct=True,
        response="hola",
        review_duration_ms=1500,
    )
    assert review["rating"] == "good"
    assert review["correct"] is True
    assert review["response"] == "hola"
    assert review["review_duration_ms"] == 1500
    assert review["reviewed_at"] is not None


async def test_record_review_wrong_answer(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    review = await record_review(
        db_conn,
        user_id=user["id"],
        concept_id=concept["id"],
        exercise_type="forward_typing",
        rating="again",
        correct=False,
        response="holla",
    )
    assert review["correct"] is False
    assert review["rating"] == "again"
    assert review["review_duration_ms"] is None


async def test_get_review_history(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    await record_review(
        db_conn, user_id=user["id"], concept_id=concept["id"],
        exercise_type="forward_mc", rating="good", correct=True,
    )
    await record_review(
        db_conn, user_id=user["id"], concept_id=concept["id"],
        exercise_type="cloze", rating="hard", correct=True,
    )
    history = await get_review_history(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    assert len(history) == 2
    # Both reviews are present (order may be non-deterministic when reviewed_at is equal)
    exercise_types = {h["exercise_type"] for h in history}
    assert exercise_types == {"cloze", "forward_mc"}
