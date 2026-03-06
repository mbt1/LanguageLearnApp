# SPDX-License-Identifier: Apache-2.0
"""Tests for content domain Pydantic schemas."""
from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from content.schemas import (
    CefrLevel,
    ConceptDetail,
    ConceptImport,
    ConceptSummary,
    ConceptType,
    CourseDetail,
    CourseImport,
    CourseImportResponse,
    CourseResponse,
    DependencySource,
    ExerciseImport,
    ExerciseResponse,
    ExerciseType,
    PrerequisiteInfo,
)

# ── Enum tests ───────────────────────────────────────────────


class TestEnums:
    def test_cefr_levels(self) -> None:
        assert [e.value for e in CefrLevel] == ["A1", "A2", "B1", "B2", "C1", "C2"]

    def test_concept_types(self) -> None:
        assert set(ConceptType) == {ConceptType.vocabulary, ConceptType.grammar}

    def test_exercise_types(self) -> None:
        assert set(ExerciseType) == {
            ExerciseType.forward_mc,
            ExerciseType.reverse_mc,
            ExerciseType.cloze,
            ExerciseType.reverse_cloze,
            ExerciseType.forward_typing,
            ExerciseType.reverse_typing,
        }

    def test_dependency_sources(self) -> None:
        assert set(DependencySource) == {DependencySource.manual, DependencySource.auto}


# ── Response model tests ─────────────────────────────────────


class TestCourseResponse:
    def test_valid(self) -> None:
        c = CourseResponse(
            id=uuid4(),
            slug="en-es",
            title="English to Spanish",
            source_language="en",
            target_language="es",
            created_at="2026-01-01T00:00:00Z",
        )
        assert c.slug == "en-es"

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            CourseResponse(  # pyright: ignore[reportCallIssue]
                id=uuid4(),
                slug="en-es",
                # missing title
                source_language="en",
                target_language="es",
                created_at="2026-01-01T00:00:00Z",
            )


class TestConceptSummary:
    def test_valid(self) -> None:
        s = ConceptSummary(
            id=uuid4(),
            concept_type=ConceptType.vocabulary,
            cefr_level=CefrLevel.A1,
            sequence=1,
            source_text="hello",
            target_text="hola",
        )
        assert s.cefr_level == CefrLevel.A1

    def test_invalid_cefr_level(self) -> None:
        with pytest.raises(ValidationError):
            ConceptSummary(
                id=uuid4(),
                concept_type=ConceptType.vocabulary,
                cefr_level="X9",  # pyright: ignore[reportArgumentType]
                sequence=1,
                source_text="hello",
                target_text="hola",
            )


class TestConceptDetail:
    def test_valid_with_prerequisites_and_exercises(self) -> None:
        detail = ConceptDetail(
            id=uuid4(),
            concept_type=ConceptType.grammar,
            cefr_level=CefrLevel.A2,
            sequence=1,
            source_text="ser vs estar",
            target_text="to be",
            explanation="Both mean 'to be' but...",
            prerequisites=[
                PrerequisiteInfo(
                    concept_id=uuid4(),
                    source_text="hello",
                    target_text="hola",
                    cefr_level=CefrLevel.A1,
                    source=DependencySource.manual,
                )
            ],
            exercises=[
                ExerciseResponse(
                    id=uuid4(),
                    exercise_type="forward_mc",
                    ref="ser-estar-mc-1",
                    data={"correct_answer": "ser", "distractors_medium": ["ir", "hacer"]},
                )
            ],
        )
        assert len(detail.prerequisites) == 1
        assert len(detail.exercises) == 1

    def test_empty_prerequisites_and_exercises(self) -> None:
        detail = ConceptDetail(
            id=uuid4(),
            concept_type=ConceptType.vocabulary,
            cefr_level=CefrLevel.A1,
            sequence=1,
            source_text="hello",
            target_text="hola",
            explanation=None,
            prerequisites=[],
            exercises=[],
        )
        assert detail.prerequisites == []


class TestCourseDetail:
    def test_valid_with_grouped_concepts(self) -> None:
        cd = CourseDetail(
            id=uuid4(),
            slug="en-es",
            title="English to Spanish",
            source_language="en",
            target_language="es",
            created_at="2026-01-01T00:00:00Z",
            concepts_by_level={
                CefrLevel.A1: [
                    ConceptSummary(
                        id=uuid4(),
                        concept_type=ConceptType.vocabulary,
                        cefr_level=CefrLevel.A1,
                        sequence=1,
                        source_text="hello",
                        target_text="hola",
                    )
                ],
            },
        )
        assert CefrLevel.A1 in cd.concepts_by_level
        assert len(cd.concepts_by_level[CefrLevel.A1]) == 1


# ── Import model tests ───────────────────────────────────────


class TestExerciseImport:
    def test_valid_forward_mc(self) -> None:
        e = ExerciseImport(
            ref="hola-mc-1",
            exercise_type="forward_mc",
            data={"correct_answer": "hola", "distractors_medium": ["adiós", "gracias"]},
        )
        assert e.data["distractors_medium"] == ["adiós", "gracias"]

    def test_valid_forward_typing(self) -> None:
        e = ExerciseImport(
            ref="hola-typing-1",
            exercise_type="forward_typing",
            data={"correct_answer": "hola"},
        )
        assert e.ref == "hola-typing-1"

    def test_missing_required_ref(self) -> None:
        with pytest.raises(ValidationError):
            ExerciseImport(  # pyright: ignore[reportCallIssue]
                exercise_type="cloze",
                data={"expected": "hola"},
            )


class TestConceptImport:
    def test_valid_with_prerequisites(self) -> None:
        c = ConceptImport(
            ref="ser-estar",
            concept_type=ConceptType.grammar,
            cefr_level=CefrLevel.A2,
            sequence=1,
            source_text="ser vs estar",
            target_text="to be",
            explanation="Both mean 'to be'...",
            prerequisites=["hola", "buenos-dias"],
            exercises=[
                ExerciseImport(
                    ref="ser-estar-mc-1",
                    exercise_type="forward_mc",
                    data={"correct_answer": "es", "distractors_medium": ["está", "son"]},
                )
            ],
        )
        assert c.prerequisites == ["hola", "buenos-dias"]

    def test_valid_no_prerequisites(self) -> None:
        c = ConceptImport(
            ref="hola",
            concept_type=ConceptType.vocabulary,
            cefr_level=CefrLevel.A1,
            sequence=1,
            source_text="hello",
            target_text="hola",
            exercises=[
                ExerciseImport(
                    ref="hola-mc-1",
                    exercise_type="forward_mc",
                    data={"correct_answer": "hola", "distractors_medium": ["adiós"]},
                ),
            ],
        )
        assert c.prerequisites is None

    def test_empty_exercises_allowed(self) -> None:
        """Empty exercises list is now allowed (exercises are optional)."""
        c = ConceptImport(
            ref="hola",
            concept_type=ConceptType.vocabulary,
            cefr_level=CefrLevel.A1,
            sequence=1,
            source_text="hello",
            target_text="hola",
            exercises=[],
        )
        assert c.exercises == []


class TestCourseImport:
    def test_valid(self) -> None:
        ci = CourseImport(
            slug="en-es",
            title="English to Spanish",
            source_language="en",
            target_language="es",
            concepts=[
                ConceptImport(
                    ref="hola",
                    concept_type=ConceptType.vocabulary,
                    cefr_level=CefrLevel.A1,
                    sequence=1,
                    source_text="hello",
                    target_text="hola",
                    exercises=[
                        ExerciseImport(
                            ref="hola-mc-1",
                            exercise_type="forward_mc",
                            data={"correct_answer": "hola", "distractors_medium": ["adiós"]},
                        ),
                    ],
                ),
            ],
        )
        assert len(ci.concepts) == 1

    def test_empty_concepts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CourseImport(
                slug="en-es",
                title="English to Spanish",
                source_language="en",
                target_language="es",
                concepts=[],
            )

    def test_missing_slug(self) -> None:
        with pytest.raises(ValidationError):
            CourseImport(  # pyright: ignore[reportCallIssue]
                title="English to Spanish",
                source_language="en",
                target_language="es",
                concepts=[
                    ConceptImport(
                        ref="hola",
                        concept_type=ConceptType.vocabulary,
                        cefr_level=CefrLevel.A1,
                        sequence=1,
                        source_text="hello",
                        target_text="hola",
                        exercises=[
                            ExerciseImport(
                                ref="hola-mc-1",
                                exercise_type="forward_mc",
                                data={"correct_answer": "hola", "distractors_medium": ["adiós"]},
                            ),
                        ],
                    ),
                ],
            )


class TestCourseImportResponse:
    def test_valid(self) -> None:
        r = CourseImportResponse(
            course_id=uuid4(),
            concepts_created=10,
            exercises_created=25,
        )
        assert r.concepts_created == 10
