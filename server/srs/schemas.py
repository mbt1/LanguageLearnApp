# SPDX-License-Identifier: Apache-2.0
"""Pydantic schemas for the SRS / study domain."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from typing import Any

from content.schemas import CefrLevel, ConceptType, ExerciseType  # noqa: TC001

# ── Study session ─────────────────────────────────────────


class StudySessionRequest(BaseModel):
    course_id: UUID
    session_size: int = Field(default=20, ge=1, le=100)
    concept_ids: list[UUID] | None = None


class StudySessionItem(BaseModel):
    concept_id: UUID
    exercise_type: ExerciseType
    is_review: bool
    source_text: str
    target_text: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    exercise_id: UUID | None = None
    exercise_data: dict[str, Any] | None = None
    correct_answer: str | None = None
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
    new_forward_difficulty: ExerciseType
    forward_consecutive_correct: int
    new_reverse_difficulty: ExerciseType
    reverse_consecutive_correct: int
    is_mastered: bool
    fsrs_due: datetime | None
    difficulty_advanced: bool
    mastery_changed: bool


# ── Exercise submission (server-graded) ───────────────────


class ExerciseSubmitRequest(BaseModel):
    concept_id: UUID
    exercise_type: ExerciseType
    user_answer: str
    exercise_id: UUID | None = None
    review_duration_ms: int | None = None


class ExerciseSubmitResponse(BaseModel):
    correct: bool
    correct_answer: str           # original (un-normalized) correct answer for display
    normalized_user_answer: str   # the string that was actually graded
    new_forward_difficulty: ExerciseType
    forward_consecutive_correct: int
    new_reverse_difficulty: ExerciseType
    reverse_consecutive_correct: int
    is_mastered: bool
    fsrs_due: datetime | None
    difficulty_advanced: bool
    mastery_changed: bool


# ── Progress ──────────────────────────────────────────────


class CefrProgressItem(BaseModel):
    cefr_level: CefrLevel
    total_concepts: int
    not_started: int
    seen: int        # forward_mc level
    familiar: int    # cloze level
    practiced: int   # forward_typing, reverse not done
    proficient: int  # both tracks maxed, not yet mastered
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
    source_text: str
    target_text: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    forward_difficulty: str | None = None
    forward_consecutive_correct: int | None = None
    reverse_difficulty: str | None = None
    reverse_consecutive_correct: int | None = None
    is_mastered: bool | None = None
    fsrs_state: str | None = None
    fsrs_stability: float | None = None
    fsrs_difficulty: float | None = None
    fsrs_due: datetime | None = None
    fsrs_last_review: datetime | None = None


class ReviewScheduleResponse(BaseModel):
    course_id: UUID
    items: list[ConceptProgressDetail]
