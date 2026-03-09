# SPDX-License-Identifier: Apache-2.0
"""Integration tests for course import service (requires DB)."""
from __future__ import annotations

from typing import Any

import psycopg
import pytest
from psycopg import AsyncConnection

from content.import_service import import_course
from content.schemas import (
    CefrLevel,
    ConceptImport,
    ConceptType,
    CourseImport,
    ExerciseImport,
)
from db.queries.concepts import get_prerequisites, list_concepts_by_course
from db.queries.courses import get_course
from db.queries.exercises import get_exercises_for_concept


def _make_concept(
    ref: str,
    *,
    concept_type: ConceptType = ConceptType.vocabulary,
    cefr_level: CefrLevel = CefrLevel.A1,
    sequence: int = 1,
    prerequisites: list[str] | None = None,
    exercises: list[ExerciseImport] | None = None,
) -> ConceptImport:
    return ConceptImport(
        ref=ref,
        concept_type=concept_type,
        cefr_level=cefr_level,
        sequence=sequence,
        prerequisites=prerequisites,
        exercises=exercises
        or [
            ExerciseImport(
                ref=f"{ref}-mc-1",
                exercise_type="forward_mc",
                data={
                    "source": f"source-{ref}",
                    "targets": [f"target-{ref}"],
                    "distractors": {"random": ["wrong1", "wrong2"]},
                },
            ),
        ],
    )


def _make_course(
    concepts: list[ConceptImport],
    slug: str = "test-course",
) -> CourseImport:
    return CourseImport(
        slug=slug,
        title="Test Course",
        source_language="en",
        target_language="es",
        concepts=concepts,
    )


# ── Happy path ────────────────────────────────────────────────


async def test_import_simple_course(db_conn: AsyncConnection[Any]) -> None:
    """Import a course with 3 concepts, 2 prerequisites, verify all rows."""
    data = _make_course(
        [
            _make_concept("hola", sequence=1),
            _make_concept("buenos-dias", sequence=2, prerequisites=["hola"]),
            _make_concept(
                "como-estas",
                sequence=3,
                prerequisites=["hola", "buenos-dias"],
            ),
        ],
    )

    result = await import_course(db_conn, data)

    assert result.concepts_created == 3
    assert result.exercises_created == 3

    # Verify course exists
    course = await get_course(db_conn, course_id=result.course_id)
    assert course is not None
    assert course["slug"] == "test-course"

    # Verify concepts exist
    concepts = await list_concepts_by_course(
        db_conn, course_id=result.course_id
    )
    assert len(concepts) == 3

    # Find the como-estas concept and verify prerequisites
    como = next(c for c in concepts if c["ref"] == "como-estas")
    prereqs = await get_prerequisites(db_conn, concept_id=como["id"])
    assert len(prereqs) == 2


async def test_import_with_exercises(db_conn: AsyncConnection[Any]) -> None:
    """Import a concept with multiple exercise types."""
    data = _make_course(
        [
            ConceptImport(
                ref="hola",
                concept_type=ConceptType.vocabulary,
                cefr_level=CefrLevel.A1,
                sequence=1,
                exercises=[
                    ExerciseImport(
                        ref="hola-mc-1",
                        exercise_type="forward_mc",
                        data={
                            "source": "hello",
                            "targets": ["hola"],
                            "distractors": {"random": ["adiós", "gracias"]},
                        },
                    ),
                    ExerciseImport(
                        ref="hola-typing-1",
                        exercise_type="forward_typing",
                        data={"source": "hello", "targets": ["hola"]},
                    ),
                ],
            )
        ],
        slug="exercise-test",
    )

    result = await import_course(db_conn, data)
    assert result.exercises_created == 2

    concepts = await list_concepts_by_course(
        db_conn, course_id=result.course_id
    )
    exercises = await get_exercises_for_concept(
        db_conn, concept_id=concepts[0]["id"]
    )
    assert len(exercises) == 2


# ── Validation errors ────────────────────────────────────────


async def test_duplicate_ref_values(db_conn: AsyncConnection[Any]) -> None:
    """Duplicate ref values should raise ValueError."""
    data = _make_course(
        [
            _make_concept("hola", sequence=1),
            _make_concept("hola", sequence=2),
        ],
    )
    with pytest.raises(ValueError, match="Duplicate ref"):
        await import_course(db_conn, data)


async def test_unknown_prerequisite_ref(
    db_conn: AsyncConnection[Any],
) -> None:
    """Prerequisite referencing unknown ref should raise ValueError."""
    data = _make_course(
        [
            _make_concept("hola", sequence=1, prerequisites=["nonexistent"]),
        ],
    )
    with pytest.raises(ValueError, match="Unknown prerequisite ref"):
        await import_course(db_conn, data)


async def test_circular_dependency_detected(
    db_conn: AsyncConnection[Any],
) -> None:
    """Circular dependencies (A→B→C→A) should raise ValueError."""
    data = _make_course(
        [
            _make_concept("a", sequence=1, prerequisites=["c"]),
            _make_concept("b", sequence=2, prerequisites=["a"]),
            _make_concept("c", sequence=3, prerequisites=["b"]),
        ],
    )
    with pytest.raises(ValueError, match="Circular dependency"):
        await import_course(db_conn, data)


async def test_self_referencing_prerequisite(
    db_conn: AsyncConnection[Any],
) -> None:
    """A concept listing itself as a prerequisite should be caught."""
    data = _make_course(
        [
            _make_concept("hola", sequence=1, prerequisites=["hola"]),
        ],
    )
    with pytest.raises(ValueError, match="Circular dependency"):
        await import_course(db_conn, data)


async def test_duplicate_slug_raises(db_conn: AsyncConnection[Any]) -> None:
    """Importing two courses with the same slug should fail."""
    data = _make_course(
        [_make_concept("hola", sequence=1)],
        slug="dup-slug",
    )
    await import_course(db_conn, data)

    # Second import with same slug should fail
    data2 = _make_course(
        [_make_concept("adios", sequence=1)],
        slug="dup-slug",
    )
    with pytest.raises(psycopg.errors.UniqueViolation):
        await import_course(db_conn, data2)
