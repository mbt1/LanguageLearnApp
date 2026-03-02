# SPDX-License-Identifier: Apache-2.0
"""Pydantic schemas for the content domain (courses, concepts, exercises)."""
from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

# ── Enums ─────────────────────────────────────────────────────


class CefrLevel(StrEnum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class ConceptType(StrEnum):
    vocabulary = "vocabulary"
    grammar = "grammar"


class ExerciseType(StrEnum):
    multiple_choice = "multiple_choice"
    cloze = "cloze"
    reverse_typing = "reverse_typing"
    typing = "typing"


class DependencySource(StrEnum):
    manual = "manual"
    auto = "auto"


# ── Response models (API output) ─────────────────────────────


class CourseResponse(BaseModel):
    id: UUID
    slug: str
    title: str
    source_language: str
    target_language: str
    created_at: str


class ConceptSummary(BaseModel):
    id: UUID
    concept_type: ConceptType
    cefr_level: CefrLevel
    sequence: int
    prompt: str
    target: str


class PrerequisiteInfo(BaseModel):
    concept_id: UUID
    prompt: str
    target: str
    cefr_level: CefrLevel
    source: DependencySource


class ExerciseResponse(BaseModel):
    id: UUID
    exercise_type: ExerciseType
    prompt: str
    correct_answer: str
    distractors: list[str] | None = None
    sentence_template: str | None = None


class ConceptDetail(BaseModel):
    id: UUID
    concept_type: ConceptType
    cefr_level: CefrLevel
    sequence: int
    prompt: str
    target: str
    explanation: str | None = None
    prerequisites: list[PrerequisiteInfo]
    exercises: list[ExerciseResponse]


class CourseDetail(CourseResponse):
    concepts_by_level: dict[CefrLevel, list[ConceptSummary]]


# ── Import models (JSON upload) ──────────────────────────────


class ExerciseImport(BaseModel):
    exercise_type: ExerciseType
    prompt: str
    correct_answer: str
    distractors: list[str] | None = None
    sentence_template: str | None = None


class ConceptImport(BaseModel):
    ref: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    sequence: int
    prompt: str
    target: str
    explanation: str | None = None
    prerequisites: list[str] | None = None
    exercises: list[ExerciseImport] = Field(min_length=1)


class CourseImport(BaseModel):
    slug: str
    title: str
    source_language: str
    target_language: str
    concepts: list[ConceptImport] = Field(min_length=1)


class CourseImportResponse(BaseModel):
    course_id: UUID
    concepts_created: int
    exercises_created: int
