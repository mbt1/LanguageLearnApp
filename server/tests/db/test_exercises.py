# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from typing import Any

import pytest
from psycopg import AsyncConnection

from db.queries.concepts import create_concept
from db.queries.courses import create_course
from db.queries.exercises import create_exercise, get_exercises_for_concept


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


async def test_create_exercise_multiple_choice(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        concept_id=concept["id"],
        exercise_type="multiple_choice",
        prompt="What is 'hello' in Spanish?",
        correct_answer="hola",
        distractors=["adiós", "gracias", "por favor"],
    )
    assert exercise["exercise_type"] == "multiple_choice"
    assert exercise["correct_answer"] == "hola"
    assert exercise["distractors"] == ["adiós", "gracias", "por favor"]


async def test_create_exercise_cloze(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        concept_id=concept["id"],
        exercise_type="cloze",
        prompt="Fill in the blank",
        correct_answer="hola",
        sentence_template="___ amigo, ¿cómo estás?",
    )
    assert exercise["exercise_type"] == "cloze"
    assert exercise["sentence_template"] == "___ amigo, ¿cómo estás?"


async def test_create_exercise_typing(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    exercise = await create_exercise(
        db_conn,
        concept_id=concept["id"],
        exercise_type="typing",
        prompt="Type 'hello' in Spanish",
        correct_answer="hola",
    )
    assert exercise["exercise_type"] == "typing"
    assert exercise["distractors"] is None
    assert exercise["sentence_template"] is None


async def test_get_exercises_for_concept(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    await create_exercise(
        db_conn, concept_id=concept["id"], exercise_type="multiple_choice",
        prompt="MC prompt", correct_answer="hola",
        distractors=["a", "b", "c"],
    )
    await create_exercise(
        db_conn, concept_id=concept["id"], exercise_type="typing",
        prompt="Typing prompt", correct_answer="hola",
    )
    exercises = await get_exercises_for_concept(db_conn, concept_id=concept["id"])
    assert len(exercises) == 2
    types = [e["exercise_type"] for e in exercises]
    assert "multiple_choice" in types
    assert "typing" in types


async def test_duplicate_exercise_type_rejected(
    db_conn: AsyncConnection, concept: dict,
) -> None:
    import psycopg.errors

    await create_exercise(
        db_conn, concept_id=concept["id"], exercise_type="typing",
        prompt="prompt1", correct_answer="hola",
    )
    with pytest.raises(psycopg.errors.UniqueViolation):
        await create_exercise(
            db_conn, concept_id=concept["id"], exercise_type="typing",
            prompt="prompt2", correct_answer="hola",
        )
