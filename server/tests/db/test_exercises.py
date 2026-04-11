# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from typing import Any

import pytest
from psycopg import AsyncConnection

from db.queries.concepts import create_concept
from db.queries.courses import create_course
from db.queries.exercises import (
    create_exercise,
    create_exercise_concept,
    get_exercise_by_type,
    get_exercises_for_concept,
)


@pytest.fixture
async def course(db_conn: AsyncConnection) -> dict[str, Any]:
    return await create_course(
        db_conn,
        slug="en-es",
        title="English to Spanish",
        source_language="en",
        target_language="es",
    )


@pytest.fixture
async def concept(db_conn: AsyncConnection, course: dict[str, Any]) -> dict[str, Any]:
    return await create_concept(
        db_conn,
        course_id=course["id"],
        concept_type="vocabulary",
        cefr_level="A1",
        sequence=1,
        ref="hello",
    )


async def test_create_exercise_translate(
    db_conn: AsyncConnection,
    concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        exercise_type="translate",
        ref="hello-translate",
        data={
            "prompt": ["hello"],
            "answers": [["hola"]],
            "distractors": {"semantic": ["adios", "gracias", "por favor"]},
        },
    )
    await create_exercise_concept(
        db_conn,
        exercise_id=exercise["id"],
        concept_id=concept["id"],
    )
    assert exercise["exercise_type"] == "translate"
    assert exercise["data"]["prompt"] == ["hello"]
    assert exercise["data"]["answers"] == [["hola"]]
    assert exercise["data"]["distractors"]["semantic"] == ["adios", "gracias", "por favor"]


async def test_create_exercise_cloze(
    db_conn: AsyncConnection,
    concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        exercise_type="cloze",
        ref="hello-cloze",
        data={"prompt": ["___ amigo, como estas?"], "answers": [["hola"]]},
    )
    await create_exercise_concept(db_conn, exercise_id=exercise["id"], concept_id=concept["id"])
    assert exercise["exercise_type"] == "cloze"
    assert exercise["data"]["prompt"] == ["___ amigo, como estas?"]


async def test_create_exercise_reverse_translate(
    db_conn: AsyncConnection,
    concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        exercise_type="translate",
        ref="hello-reverse",
        reverse=True,
        data={"prompt": ["hola"], "answers": [["hello"]]},
    )
    await create_exercise_concept(db_conn, exercise_id=exercise["id"], concept_id=concept["id"])
    assert exercise["exercise_type"] == "translate"
    assert exercise["reverse"] is True
    assert "distractors" not in exercise["data"]


async def test_get_exercises_for_concept(
    db_conn: AsyncConnection,
    concept: dict,
) -> None:
    ex1 = await create_exercise(
        db_conn,
        exercise_type="translate",
        ref="hello-translate",
        data={
            "prompt": ["hello"],
            "answers": [["hola"]],
            "distractors": {"semantic": ["a", "b", "c"]},
        },
    )
    await create_exercise_concept(db_conn, exercise_id=ex1["id"], concept_id=concept["id"])
    ex2 = await create_exercise(
        db_conn,
        exercise_type="cloze",
        ref="hello-cloze",
        data={"prompt": ["___ mundo"], "answers": [["hola"]]},
    )
    await create_exercise_concept(db_conn, exercise_id=ex2["id"], concept_id=concept["id"])
    exercises = await get_exercises_for_concept(db_conn, concept_id=concept["id"])
    assert len(exercises) == 2
    types = [e["exercise_type"] for e in exercises]
    assert "translate" in types
    assert "cloze" in types


async def test_get_exercise_by_type_returns_row(
    db_conn: AsyncConnection,
    concept: dict,
) -> None:
    ex = await create_exercise(
        db_conn,
        exercise_type="translate",
        ref="hello-translate",
        data={"prompt": ["hello"], "answers": [["hola"]]},
    )
    await create_exercise_concept(db_conn, exercise_id=ex["id"], concept_id=concept["id"])
    row = await get_exercise_by_type(
        db_conn,
        concept_id=concept["id"],
        exercise_type="translate",
    )
    assert row is not None
    assert row["data"]["answers"] == [["hola"]]
    assert row["exercise_type"] == "translate"


async def test_get_exercise_by_type_returns_none_when_not_found(
    db_conn: AsyncConnection,
    concept: dict,
) -> None:
    row = await get_exercise_by_type(
        db_conn,
        concept_id=concept["id"],
        exercise_type="translate",
    )
    assert row is None


async def test_multiple_exercises_same_type_allowed(
    db_conn: AsyncConnection,
    concept: dict,
) -> None:
    """Multiple exercises of the same type per concept are allowed."""
    ex1 = await create_exercise(
        db_conn,
        exercise_type="translate",
        ref="hello-translate-1",
        data={"prompt": ["hello"], "answers": [["hola"]], "distractors": {"semantic": ["adios"]}},
    )
    await create_exercise_concept(db_conn, exercise_id=ex1["id"], concept_id=concept["id"])
    ex2 = await create_exercise(
        db_conn,
        exercise_type="translate",
        ref="hello-translate-2",
        data={"prompt": ["hello"], "answers": [["hola"]], "distractors": {"semantic": ["gracias"]}},
    )
    await create_exercise_concept(db_conn, exercise_id=ex2["id"], concept_id=concept["id"])
    exercises = await get_exercises_for_concept(db_conn, concept_id=concept["id"])
    translate_exercises = [e for e in exercises if e["exercise_type"] == "translate"]
    assert len(translate_exercises) == 2
