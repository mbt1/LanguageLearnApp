# SPDX-License-Identifier: Apache-2.0
"""Pydantic schemas for the content domain (courses, concepts, exercises)."""
from __future__ import annotations

from enum import StrEnum
from typing import Any
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
    translate = "translate"
    cloze = "cloze"
    match = "match"


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
    ref: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    sequence: int


class PrerequisiteInfo(BaseModel):
    concept_id: UUID
    ref: str
    cefr_level: CefrLevel
    source: DependencySource


class ExerciseResponse(BaseModel):
    id: UUID
    exercise_type: str
    ref: str
    data: dict[str, Any]


class ConceptDetail(BaseModel):
    id: UUID
    ref: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    sequence: int
    explanation: str | None = None
    prerequisites: list[PrerequisiteInfo]
    exercises: list[ExerciseResponse]


class CourseDetail(CourseResponse):
    concepts_by_level: dict[CefrLevel, list[ConceptSummary]]


# ── Import models (JSON upload) ──────────────────────────────


class ExerciseImport(BaseModel):
    ref: str
    exercise_type: str
    reverse: bool = False
    data: dict[str, Any] = Field(default_factory=dict)
    concept_refs: list[str] | None = None  # for multi-concept exercises


class ConceptImport(BaseModel):
    ref: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    sequence: int
    explanation: str | None = None
    prerequisites: list[str] | None = None
    exercises: list[ExerciseImport] = Field(default_factory=list)


class CourseImport(BaseModel):
    """Assembled course data (may come from a single JSON or a folder)."""
    slug: str
    title: str
    source_language: str
    target_language: str
    concepts: list[ConceptImport] = Field(min_length=1)
    standalone_exercises: list[ExerciseImport] = Field(default_factory=list)


class CourseImportResponse(BaseModel):
    course_id: UUID
    concepts_created: int
    exercises_created: int
