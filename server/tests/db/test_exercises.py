# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from typing import Any

import pytest
from psycopg import AsyncConnection

from db.queries.concepts import create_concept
from db.queries.courses import create_course
from db.queries.exercises import create_exercise, create_exercise_concept, get_exercise_by_type, get_exercises_for_concept


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


async def test_create_exercise_forward_mc(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        exercise_type="forward_mc",
        ref="hello-mc",
        data={"correct_answer": "hola", "distractors": ["adios", "gracias", "por favor"]},
    )
    await create_exercise_concept(db_conn, exercise_id=exercise["id"], concept_id=concept["id"])
    assert exercise["exercise_type"] == "forward_mc"
    assert exercise["data"]["correct_answer"] == "hola"
    assert exercise["data"]["distractors"] == ["adios", "gracias", "por favor"]


async def test_create_exercise_cloze(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        exercise_type="cloze",
        ref="hello-cloze",
        data={"correct_answer": "hola", "sentence_template": "___ amigo, como estas?"},
    )
    await create_exercise_concept(db_conn, exercise_id=exercise["id"], concept_id=concept["id"])
    assert exercise["exercise_type"] == "cloze"
    assert exercise["data"]["sentence_template"] == "___ amigo, como estas?"


async def test_create_exercise_forward_typing(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        exercise_type="forward_typing",
        ref="hello-typing",
        data={"correct_answer": "hola"},
    )
    await create_exercise_concept(db_conn, exercise_id=exercise["id"], concept_id=concept["id"])
    assert exercise["exercise_type"] == "forward_typing"
    assert "distractors" not in exercise["data"]
    assert "sentence_template" not in exercise["data"]


async def test_get_exercises_for_concept(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    ex1 = await create_exercise(
        db_conn, exercise_type="forward_mc", ref="hello-mc",
        data={"correct_answer": "hola", "distractors": ["a", "b", "c"]},
    )
    await create_exercise_concept(db_conn, exercise_id=ex1["id"], concept_id=concept["id"])
    ex2 = await create_exercise(
        db_conn, exercise_type="forward_typing", ref="hello-typing",
        data={"correct_answer": "hola"},
    )
    await create_exercise_concept(db_conn, exercise_id=ex2["id"], concept_id=concept["id"])
    exercises = await get_exercises_for_concept(db_conn, concept_id=concept["id"])
    assert len(exercises) == 2
    types = [e["exercise_type"] for e in exercises]
    assert "forward_mc" in types
    assert "forward_typing" in types


async def test_get_exercise_by_type_returns_row(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    ex = await create_exercise(
        db_conn, exercise_type="forward_typing", ref="hello-typing",
        data={"correct_answer": "hola"},
    )
    await create_exercise_concept(db_conn, exercise_id=ex["id"], concept_id=concept["id"])
    row = await get_exercise_by_type(
        db_conn, concept_id=concept["id"], exercise_type="forward_typing",
    )
    assert row is not None
    assert row["data"]["correct_answer"] == "hola"
    assert row["exercise_type"] == "forward_typing"


async def test_get_exercise_by_type_returns_none_when_not_found(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    row = await get_exercise_by_type(
        db_conn, concept_id=concept["id"], exercise_type="forward_typing",
    )
    assert row is None


async def test_multiple_exercises_same_type_allowed(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    """Multiple exercises of the same type per concept are allowed."""
    ex1 = await create_exercise(
        db_conn, exercise_type="forward_mc", ref="hello-mc-1",
        data={"correct_answer": "hola", "distractors": ["adios"]},
    )
    await create_exercise_concept(db_conn, exercise_id=ex1["id"], concept_id=concept["id"])
    ex2 = await create_exercise(
        db_conn, exercise_type="forward_mc", ref="hello-mc-2",
        data={"correct_answer": "hola", "distractors": ["gracias"]},
    )
    await create_exercise_concept(db_conn, exercise_id=ex2["id"], concept_id=concept["id"])
    exercises = await get_exercises_for_concept(db_conn, concept_id=concept["id"])
    mc_exercises = [e for e in exercises if e["exercise_type"] == "forward_mc"]
    assert len(mc_exercises) == 2
