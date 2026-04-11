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
    concept_ids: list[UUID] | None = None


class StudySessionItem(BaseModel):
    concept_id: UUID
    exercise_type: ExerciseType
    difficulty: int
    presentation: str
    reverse: bool = False
    is_review: bool
    concept_type: ConceptType
    cefr_level: CefrLevel
    exercise_id: UUID | None = None
    prompt: list[str] = Field(default_factory=list)
    correct_answers: list[str] = Field(default_factory=list)
    distractors: list[str] | None = None
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
    difficulty: int
    response: str | None = None
    correct: bool
    review_duration_ms: int | None = None


class ReviewResponse(BaseModel):
    concept_id: UUID
    difficulty: int
    peak_difficulty: int
    is_mastered: bool
    fsrs_due: datetime | None
    mastery_changed: bool


# ── Exercise submission (server-graded) ───────────────────


class ExerciseSubmitRequest(BaseModel):
    concept_id: UUID
    exercise_type: ExerciseType
    difficulty: int
    user_answer: str
    exercise_id: UUID | None = None
    review_duration_ms: int | None = None


class ExerciseSubmitResponse(BaseModel):
    correct: bool
    correct_answer: str
    normalized_user_answer: str
    difficulty: int
    peak_difficulty: int
    is_mastered: bool
    fsrs_due: datetime | None
    mastery_changed: bool


# ── Progress ──────────────────────────────────────────────


class CefrProgressItem(BaseModel):
    cefr_level: CefrLevel
    total_concepts: int
    not_started: int
    seen: int  # difficulty 10
    familiar: int  # difficulty 20-30
    practiced: int  # difficulty 40-50
    proficient: int  # max difficulty, not yet mastered
    mastered: int


class CourseProgressResponse(BaseModel):
    course_id: UUID
    levels: list[CefrProgressItem]


class AllProgressResponse(BaseModel):
    courses: list[CourseProgressResponse]


# ── Review schedule ──────────────────────────────────────


class ConceptProgressDetail(BaseModel):
    """Full SRS detail for a single concept (started or unstarted)."""

    concept_id: UUID
    ref: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    peak_difficulty: int | None = None
    is_mastered: bool | None = None
    fsrs_state: str | None = None
    fsrs_stability: float | None = None
    fsrs_difficulty: float | None = None
    fsrs_due: datetime | None = None
    fsrs_last_review: datetime | None = None


class ReviewScheduleResponse(BaseModel):
    course_id: UUID
    items: list[ConceptProgressDetail]
