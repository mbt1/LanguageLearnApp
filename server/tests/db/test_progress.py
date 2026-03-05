# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

import datetime
from typing import Any

import pytest
from psycopg import AsyncConnection

from db.queries.concepts import add_prerequisite, create_concept
from db.queries.courses import create_course
from db.queries.progress import (
    get_prerequisite_difficulties,
    get_prerequisite_difficulties_batch,
    get_progress,
    get_progress_summary,
    list_all_active_progress,
    list_all_progress_detail,
    list_due_reviews,
    list_new_concepts,
    upsert_progress,
)
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


# ── get_prerequisite_difficulties ────────────────────────────

async def test_prerequisite_difficulties_no_prerequisites(
    db_conn: AsyncConnection, user: dict, concept: dict,
) -> None:
    rows = await get_prerequisite_difficulties(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    assert rows == []


async def test_prerequisite_difficulties_unstarted_defaults_to_multiple_choice(
    db_conn: AsyncConnection, user: dict, course: dict, concept: dict,
) -> None:
    prereq = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="bye", target="adiós",
    )
    await add_prerequisite(db_conn, concept_id=concept["id"], prerequisite_id=prereq["id"])

    rows = await get_prerequisite_difficulties(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    assert len(rows) == 1
    assert rows[0]["current_exercise_difficulty"] == "multiple_choice"


async def test_prerequisite_difficulties_reflects_actual_progress(
    db_conn: AsyncConnection, user: dict, course: dict, concept: dict,
) -> None:
    prereq = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="bye", target="adiós",
    )
    await add_prerequisite(db_conn, concept_id=concept["id"], prerequisite_id=prereq["id"])
    await upsert_progress(
        db_conn, user_id=user["id"], concept_id=prereq["id"],
        current_exercise_difficulty="cloze",
    )

    rows = await get_prerequisite_difficulties(
        db_conn, user_id=user["id"], concept_id=concept["id"],
    )
    assert rows[0]["current_exercise_difficulty"] == "cloze"


# ── get_prerequisite_difficulties_batch ──────────────────────

async def test_prerequisite_difficulties_batch_empty_list(
    db_conn: AsyncConnection, user: dict,
) -> None:
    result = await get_prerequisite_difficulties_batch(db_conn, user_id=user["id"], concept_ids=[])
    assert result == {}


async def test_prerequisite_difficulties_batch_groups_by_concept(
    db_conn: AsyncConnection, user: dict, course: dict,
) -> None:
    c1 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="a", target="a",
    )
    c2 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="b", target="b",
    )
    child = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A2", sequence=1, prompt="c", target="c",
    )
    await add_prerequisite(db_conn, concept_id=child["id"], prerequisite_id=c1["id"])
    await add_prerequisite(db_conn, concept_id=child["id"], prerequisite_id=c2["id"])

    result = await get_prerequisite_difficulties_batch(
        db_conn, user_id=user["id"], concept_ids=[child["id"]],
    )
    assert child["id"] in result
    assert len(result[child["id"]]) == 2


# ── list_new_concepts ─────────────────────────────────────────

async def test_list_new_concepts_returns_unstarted(
    db_conn: AsyncConnection, user: dict, course: dict,
) -> None:
    c1 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="a", target="a",
    )
    c2 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="b", target="b",
    )
    # Start c1 but not c2
    await upsert_progress(db_conn, user_id=user["id"], concept_id=c1["id"])

    rows = await list_new_concepts(db_conn, user_id=user["id"], course_id=course["id"])
    ids = [r["id"] for r in rows]
    assert c2["id"] in ids
    assert c1["id"] not in ids


# ── list_all_active_progress ──────────────────────────────────

async def test_list_all_active_progress_excludes_null_due(
    db_conn: AsyncConnection, user: dict, course: dict,
) -> None:
    now = datetime.datetime.now(tz=datetime.UTC)
    c1 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="a", target="a",
    )
    c2 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="b", target="b",
    )
    # c1 has a due date, c2 does not
    await upsert_progress(
        db_conn, user_id=user["id"], concept_id=c1["id"],
        fsrs_due=now + datetime.timedelta(days=3), fsrs_state="review",
    )
    await upsert_progress(db_conn, user_id=user["id"], concept_id=c2["id"])

    rows = await list_all_active_progress(db_conn, user_id=user["id"], course_id=course["id"])
    ids = [r["concept_id"] for r in rows]
    assert c1["id"] in ids
    assert c2["id"] not in ids


# ── get_progress_summary ──────────────────────────────────────

async def test_get_progress_summary(
    db_conn: AsyncConnection, user: dict, course: dict,
) -> None:
    c1 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="a", target="a",
    )
    c2 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="b", target="b",
    )
    # c1 mastered, c2 not
    await upsert_progress(db_conn, user_id=user["id"], concept_id=c1["id"], is_mastered=True)
    await upsert_progress(db_conn, user_id=user["id"], concept_id=c2["id"], is_mastered=False)

    rows = await get_progress_summary(db_conn, user_id=user["id"], course_id=course["id"])
    assert len(rows) == 1  # one CEFR level (A1)
    row = rows[0]
    assert row["cefr_level"] == "A1"
    assert row["total_concepts"] == 2
    assert row["mastered"] == 1
    assert row["seen"] == 1  # c2 defaults to multiple_choice, not mastered


# ── list_all_progress_detail ─────────────────────────────────

async def test_list_all_progress_detail_includes_unstarted(
    db_conn: AsyncConnection, user: dict, course: dict,
) -> None:
    """LEFT JOIN returns all concepts, including those without progress."""
    c1 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    c2 = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="goodbye", target="adiós",
    )
    # Start c1 only
    await upsert_progress(db_conn, user_id=user["id"], concept_id=c1["id"])

    rows = await list_all_progress_detail(
        db_conn, user_id=user["id"], course_id=course["id"],
    )
    assert len(rows) == 2
    by_id = {r["concept_id"]: r for r in rows}

    # Started concept has progress fields populated
    started = by_id[c1["id"]]
    assert started["current_exercise_difficulty"] == "multiple_choice"
    assert started["consecutive_correct"] == 0
    assert started["is_mastered"] is False

    # Unstarted concept has NULL progress fields
    unstarted = by_id[c2["id"]]
    assert unstarted["prompt"] == "goodbye"
    assert unstarted["current_exercise_difficulty"] is None
    assert unstarted["consecutive_correct"] is None
    assert unstarted["is_mastered"] is None
    assert unstarted["fsrs_state"] is None
    assert unstarted["fsrs_due"] is None
