# SPDX-License-Identifier: Apache-2.0
"""Pydantic schemas for the SRS / study domain."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from content.schemas import CefrLevel, ConceptType, ExerciseType  # noqa: TC001

# ── Study session ─────────────────────────────────────────


class StudySessionRequest(BaseModel):
    course_id: UUID
    session_size: int = Field(default=20, ge=1, le=100)


class StudySessionItem(BaseModel):
    concept_id: UUID
    exercise_type: ExerciseType
    is_review: bool
    prompt: str
    target: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    distractors: list[str] | None = None
    sentence_template: str | None = None
    explanation: str | None = None


class StudySessionResponse(BaseModel):
    items: list[StudySessionItem]
    total_due_reviews: int
    new_concepts_added: int


# ── Review submission ─────────────────────────────────────


class ReviewRequest(BaseModel):
    concept_id: UUID
    rating: str = Field(pattern=r"^(again|hard|good|easy)$")
    exercise_type: ExerciseType
    response: str | None = None
    correct: bool
    review_duration_ms: int | None = None


class ReviewResponse(BaseModel):
    concept_id: UUID
    new_exercise_difficulty: ExerciseType
    consecutive_correct: int
    is_mastered: bool
    fsrs_due: datetime | None
    difficulty_advanced: bool
    mastery_changed: bool


# ── Progress ──────────────────────────────────────────────


class CefrProgressItem(BaseModel):
    cefr_level: CefrLevel
    total_concepts: int
    mastered_concepts: int
    mastery_percentage: float


class CourseProgressResponse(BaseModel):
    course_id: UUID
    levels: list[CefrProgressItem]
