# SPDX-License-Identifier: Apache-2.0
"""Graded exercise submission endpoint."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser  # noqa: TC001
from content.schemas import FORWARD_TYPES, ExerciseType
from db.pool import get_conn
from db.queries.concepts import get_concept
from db.queries.exercises import get_exercise_by_id, get_exercise_by_type
from db.queries.progress import (
    get_prerequisite_difficulties,
    get_progress,
    refresh_progress_summary,
    upsert_progress,
)
from db.queries.reviews import record_review
from grading.provider import default_grader
from grading.schemas import GradingRequest, Verdict
from srs.difficulty import advance_difficulty
from srs.mastery import check_mastery_regression, compute_mastery
from srs.prerequisite_cap import compute_capped_difficulty
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

    # Resolve correct_answer from exercise JSONB data or concept
    correct_answer = _resolve_correct_answer(request.exercise_type, exercise, concept)
    if correct_answer is None:
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
            correct_answer=correct_answer,
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

    # Determine which track this exercise belongs to
    is_fwd = request.exercise_type in FORWARD_TYPES

    # Advance exercise difficulty for the relevant track
    if is_fwd:
        old_difficulty = ExerciseType(progress["forward_difficulty"])
        old_streak = progress["forward_consecutive_correct"]
    else:
        old_difficulty = ExerciseType(progress["reverse_difficulty"])
        old_streak = progress["reverse_consecutive_correct"]

    new_difficulty, new_streak = advance_difficulty(old_difficulty, old_streak, correct)
    difficulty_advanced = new_difficulty != old_difficulty

    # Apply prerequisite cap for the relevant track
    prereq_rows = await get_prerequisite_difficulties(
        conn, user_id=user_id, concept_id=concept_id,
    )
    diff_key = "forward_difficulty" if is_fwd else "reverse_difficulty"
    prereq_types = [ExerciseType(r[diff_key]) for r in prereq_rows]
    capped_difficulty = compute_capped_difficulty(new_difficulty, prereq_types)

    # Build final difficulty values
    if is_fwd:
        fwd_diff = capped_difficulty.value
        fwd_streak = new_streak
        rev_diff = progress["reverse_difficulty"]
        rev_streak = progress["reverse_consecutive_correct"]
    else:
        fwd_diff = progress["forward_difficulty"]
        fwd_streak = progress["forward_consecutive_correct"]
        rev_diff = capped_difficulty.value
        rev_streak = new_streak

    # Compute mastery (requires both tracks at max)
    was_mastered = bool(progress["is_mastered"])
    regressed = check_mastery_regression(was_mastered, correct)
    new_mastery = compute_mastery(
        forward_difficulty=fwd_diff,
        reverse_difficulty=rev_diff,
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
        forward_difficulty=fwd_diff,
        forward_consecutive_correct=fwd_streak,
        reverse_difficulty=rev_diff,
        reverse_consecutive_correct=rev_streak,
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
        correct_answer=correct_answer,
        normalized_user_answer=grading_result.normalized_user_answer,
        new_forward_difficulty=ExerciseType(fwd_diff),
        forward_consecutive_correct=fwd_streak,
        new_reverse_difficulty=ExerciseType(rev_diff),
        reverse_consecutive_correct=rev_streak,
        is_mastered=is_mastered,
        fsrs_due=review_result.fsrs_due,
        difficulty_advanced=difficulty_advanced,
        mastery_changed=mastery_changed,
    )


def _resolve_correct_answer(
    exercise_type: ExerciseType,
    exercise: dict | None,
    concept: dict,
) -> str | None:
    """Extract the correct answer from exercise JSONB data or concept fields."""
    if exercise is not None:
        data = exercise.get("data") or {}
        # Cloze exercises store expected in data
        if exercise_type in (ExerciseType.cloze, ExerciseType.reverse_cloze):
            return data.get("expected")
        # Grammar exercises may have correct_answer in data
        if data.get("correct_answer"):
            return data["correct_answer"]

    # Fall back to concept source/target text
    if exercise_type in (ExerciseType.forward_mc, ExerciseType.cloze, ExerciseType.forward_typing):
        return concept["target_text"]
    if exercise_type in (ExerciseType.reverse_mc, ExerciseType.reverse_cloze, ExerciseType.reverse_typing):
        return concept["source_text"]
    return None
