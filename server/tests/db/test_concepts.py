# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from typing import Any

import pytest
from psycopg import AsyncConnection

from db.queries.concepts import (
    add_prerequisite,
    create_concept,
    get_concept,
    get_prerequisites,
    list_concepts_by_course,
)
from db.queries.courses import create_course


@pytest.fixture
async def course(db_conn: AsyncConnection) -> dict[str, Any]:
    """Create a test course."""
    return await create_course(
        db_conn, slug="en-es", title="English to Spanish",
        source_language="en", target_language="es",
    )


async def test_create_concept(db_conn: AsyncConnection, course: dict[str, Any]) -> None:
    concept = await create_concept(
        db_conn,
        course_id=course["id"],
        concept_type="vocabulary",
        cefr_level="A1",
        sequence=1,
        prompt="hello",
        target="hola",
        explanation="A common greeting",
    )
    assert concept["prompt"] == "hello"
    assert concept["target"] == "hola"
    assert concept["concept_type"] == "vocabulary"
    assert concept["cefr_level"] == "A1"
    assert concept["sequence"] == 1


async def test_get_concept(db_conn: AsyncConnection, course: dict[str, Any]) -> None:
    concept = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    found = await get_concept(db_conn, concept_id=concept["id"])
    assert found is not None
    assert found["prompt"] == "hello"


async def test_list_concepts_by_course(db_conn: AsyncConnection, course: dict[str, Any]) -> None:
    await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=2, prompt="goodbye", target="adiós",
    )
    await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    concepts = await list_concepts_by_course(db_conn, course_id=course["id"])
    assert len(concepts) == 2
    # Ordered by sequence
    assert concepts[0]["prompt"] == "hello"
    assert concepts[1]["prompt"] == "goodbye"


async def test_list_concepts_filtered_by_level(
    db_conn: AsyncConnection, course: dict[str, Any],
) -> None:
    await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    await create_concept(
        db_conn, course_id=course["id"], concept_type="grammar",
        cefr_level="A2", sequence=1, prompt="past tense", target="pasado",
    )
    a1_concepts = await list_concepts_by_course(
        db_conn, course_id=course["id"], cefr_level="A1",
    )
    assert len(a1_concepts) == 1
    assert a1_concepts[0]["cefr_level"] == "A1"


async def test_add_prerequisite(db_conn: AsyncConnection, course: dict[str, Any]) -> None:
    prereq = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    concept = await create_concept(
        db_conn, course_id=course["id"], concept_type="grammar",
        cefr_level="A1", sequence=2, prompt="greeting phrases", target="frases",
    )
    link = await add_prerequisite(
        db_conn, concept_id=concept["id"], prerequisite_id=prereq["id"],
    )
    assert link["concept_id"] == concept["id"]
    assert link["prerequisite_id"] == prereq["id"]
    assert link["source"] == "manual"


async def test_get_prerequisites(db_conn: AsyncConnection, course: dict[str, Any]) -> None:
    prereq = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    concept = await create_concept(
        db_conn, course_id=course["id"], concept_type="grammar",
        cefr_level="A1", sequence=2, prompt="greeting phrases", target="frases",
    )
    await add_prerequisite(
        db_conn, concept_id=concept["id"], prerequisite_id=prereq["id"],
    )
    prereqs = await get_prerequisites(db_conn, concept_id=concept["id"])
    assert len(prereqs) == 1
    assert prereqs[0]["prompt"] == "hello"
    assert prereqs[0]["source"] == "manual"


async def test_self_prerequisite_rejected(
    db_conn: AsyncConnection, course: dict[str, Any],
) -> None:
    import psycopg.errors

    concept = await create_concept(
        db_conn, course_id=course["id"], concept_type="vocabulary",
        cefr_level="A1", sequence=1, prompt="hello", target="hola",
    )
    with pytest.raises(psycopg.errors.CheckViolation):
        await add_prerequisite(
            db_conn, concept_id=concept["id"], prerequisite_id=concept["id"],
        )
