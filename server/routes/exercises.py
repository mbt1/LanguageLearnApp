# SPDX-License-Identifier: Apache-2.0
"""Graded exercise submission endpoint."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser  # noqa: TC001
from db.pool import get_conn
from db.queries.concepts import get_concept
from db.queries.exercises import get_exercise_by_id, get_exercise_by_type
from db.queries.progress import (
    get_progress,
    refresh_progress_summary,
    upsert_progress,
)
from db.queries.reviews import record_review
from grading.provider import default_grader
from grading.schemas import GradingRequest, Verdict
from srs.difficulty import derive_difficulty
from srs.mastery import check_mastery_regression, compute_mastery
from srs.scheduler import Rating, process_review, reconstruct_card
from srs.schemas import ExerciseSubmitRequest, ExerciseSubmitResponse

router = APIRouter(tags=["exercises"])


@router.post("/v1/exercises/submit", response_model=ExerciseSubmitResponse)
async def submit_exercise(
    request: ExerciseSubmitRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> ExerciseSubmitResponse:
    now = datetime.now(UTC)
    user_id = current_user.user_id
    concept_id = request.concept_id

    # Fetch the specific exercise to get the correct answer
    concept = await get_concept(conn, concept_id=concept_id)
    if concept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept {concept_id} not found.",
        )

    if request.exercise_id:
        exercise = await get_exercise_by_id(conn, exercise_id=request.exercise_id)
    else:
        exercise = await get_exercise_by_type(
            conn, concept_id=concept_id, exercise_type=request.exercise_type.value,
        )

    # Resolve correct answers from exercise JSONB data
    correct_answers = _resolve_correct_answers(exercise)
    if not correct_answers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot determine correct answer for exercise "
            f"(concept_id={concept_id}, type={request.exercise_type.value}).",
        )

    # Fetch current progress — 404 if not started
    progress = await get_progress(conn, user_id=user_id, concept_id=concept_id)
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress found for this concept. Start a session first.",
        )

    # Grade the answer
    grading_result = default_grader.grade(
        GradingRequest(
            exercise_type=request.exercise_type,
            correct_answers=correct_answers,
            user_answer=request.user_answer,
        )
    )
    correct = grading_result.verdict == Verdict.accept

    # Derive FSRS rating automatically from grading result
    rating = Rating.Good if correct else Rating.Again

    # Reconstruct FSRS card and run scheduling
    card = reconstruct_card(
        fsrs_state=progress["fsrs_state"],
        fsrs_step=progress["fsrs_step"],
        fsrs_stability=progress["fsrs_stability"],
        fsrs_difficulty=progress["fsrs_difficulty"],
        fsrs_due=progress["fsrs_due"],
        fsrs_last_review=progress["fsrs_last_review"],
    )
    review_result = process_review(card, rating, now)

    # Update peak difficulty on correct answer
    old_peak = progress["peak_difficulty"]
    new_peak = max(old_peak, request.difficulty) if correct else old_peak

    # Compute mastery
    was_mastered = bool(progress["is_mastered"])
    regressed = check_mastery_regression(was_mastered, correct)
    new_mastery = compute_mastery(
        fsrs_stability=review_result.fsrs_stability,
        fsrs_state=review_result.fsrs_state,
    )
    is_mastered = new_mastery and not regressed
    mastery_changed = is_mastered != was_mastered

    # Persist progress + review history
    await upsert_progress(
        conn,
        user_id=user_id,
        concept_id=concept_id,
        peak_difficulty=new_peak,
        fsrs_state=review_result.fsrs_state,
        fsrs_step=review_result.fsrs_step,
        fsrs_stability=review_result.fsrs_stability,
        fsrs_difficulty=review_result.fsrs_difficulty,
        fsrs_due=review_result.fsrs_due,
        fsrs_last_review=review_result.fsrs_last_review,
        is_mastered=is_mastered,
    )
    await record_review(
        conn,
        user_id=user_id,
        concept_id=concept_id,
        exercise_type=request.exercise_type.value,
        rating=rating.name.lower(),
        correct=correct,
        response=request.user_answer,
        review_duration_ms=request.review_duration_ms,
    )
    # Refresh precalculated progress summary
    await refresh_progress_summary(
        conn,
        user_id=user_id,
        course_id=concept["course_id"],
        cefr_level=concept["cefr_level"],
    )
    await conn.commit()

    return ExerciseSubmitResponse(
        correct=correct,
        correct_answer=correct_answers[0],
        normalized_user_answer=grading_result.normalized_user_answer,
        difficulty=derive_difficulty(
            stability=review_result.fsrs_stability,
            peak_difficulty=new_peak,
        ),
        peak_difficulty=new_peak,
        is_mastered=is_mastered,
        fsrs_due=review_result.fsrs_due,
        mastery_changed=mastery_changed,
    )


def _resolve_correct_answers(
    exercise: dict[str, Any] | None,
) -> list[str] | None:
    """Extract correct answers from exercise JSONB data.

    New format: data.answers is a list of lists (alternatives per position).
    The first position's alternatives are the accepted answers.
    """
    if exercise is None:
        return None
    data: dict[str, Any] = exercise.get("data") or {}
    answers: list[Any] | None = data.get("answers")
    if answers and answers[0]:
        first: Any = answers[0]
        if isinstance(first, str):
            return [first]
        if isinstance(first, list):
            return list(map(str, first))
    return None
