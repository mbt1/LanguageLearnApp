# SPDX-License-Identifier: Apache-2.0
"""Study session and review submission endpoints."""
from __future__ import annotations

import random
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser  # noqa: TC001
from content.schemas import CefrLevel, ExerciseType
from dataclasses import replace

from db.pool import get_conn
from db.queries.courses import get_course
from db.queries.exercises import get_exercises_for_session
from db.queries.progress import (
    get_all_progress_summary,
    get_prerequisite_difficulties,
    get_prerequisite_difficulties_batch,
    get_progress,
    get_progress_summary,
    list_all_active_progress,
    list_due_reviews,
    list_new_concepts,
    upsert_progress,
)
from db.queries.reviews import record_review
from srs.difficulty import advance_difficulty
from srs.mastery import check_mastery_regression, compute_mastery
from srs.prerequisite_cap import compute_capped_difficulty
from srs.scheduler import (
    parse_rating,
    process_review,
    reconstruct_card,
)
from srs.schemas import (
    AllProgressResponse,
    CefrProgressItem,
    CourseProgressResponse,
    ReviewRequest,
    ReviewResponse,
    StudySessionItem,
    StudySessionRequest,
    StudySessionResponse,
)
from srs.session import SessionItem, build_session

router = APIRouter(tags=["study"])


# ── POST /v1/study/session ────────────────────────────────────


@router.post("/v1/study/session", response_model=StudySessionResponse)
async def create_study_session(
    request: StudySessionRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> StudySessionResponse:
    now = datetime.now(UTC)
    user_id = current_user.user_id
    course_id = request.course_id

    # Verify course exists
    course = await get_course(conn, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    # Fetch data for session building
    due_reviews = await list_due_reviews(
        conn, user_id=user_id, now=now, limit=request.session_size,
    )
    new_concepts = await list_new_concepts(
        conn, user_id=user_id, course_id=course_id, limit=request.session_size,
    )
    all_active = await list_all_active_progress(conn, user_id=user_id, course_id=course_id)

    # Batch fetch prerequisite difficulties for due reviews
    review_concept_ids = [r["concept_id"] for r in due_reviews]
    prereq_map = await get_prerequisite_difficulties_batch(
        conn, user_id=user_id, concept_ids=review_concept_ids,
    )

    # Build session
    items = build_session(
        due_reviews=due_reviews,
        new_concepts=new_concepts,
        prereq_difficulties=prereq_map,
        all_active_progress=all_active,
        session_size=request.session_size,
    )

    # Batch fetch exercise-specific data (distractors, sentence_template, exercise_id)
    exercise_keys = [(item.concept_id, item.exercise_type.value) for item in items]
    exercise_map = await get_exercises_for_session(conn, items=exercise_keys)
    enriched_items: list[SessionItem] = []
    for item in items:
        exercises = exercise_map.get((item.concept_id, item.exercise_type.value))
        if exercises:
            ex = random.choice(exercises)  # noqa: S311
            enriched_items.append(replace(
                item,
                exercise_id=ex["id"],
                correct_answer=ex.get("correct_answer"),
                distractors=ex.get("distractors"),
                sentence_template=ex.get("sentence_template"),
            ))
        else:
            enriched_items.append(item)
    items = enriched_items

    # Create initial progress rows for new concepts added to session
    new_items = [item for item in items if not item.is_review]
    for item in new_items:
        await upsert_progress(
            conn,
            user_id=user_id,
            concept_id=item.concept_id,
            fsrs_due=now,
        )
    await conn.commit()

    return StudySessionResponse(
        items=_items_to_response(items),
        total_due_reviews=len(due_reviews),
        new_concepts_added=len(new_items),
    )


def _items_to_response(items: list[SessionItem]) -> list[StudySessionItem]:
    return [
        StudySessionItem(
            concept_id=item.concept_id,
            exercise_type=item.exercise_type,
            is_review=item.is_review,
            prompt=item.prompt,
            target=item.target,
            concept_type=item.concept_type,
            cefr_level=item.cefr_level,
            exercise_id=item.exercise_id,
            correct_answer=item.correct_answer,
            distractors=item.distractors,
            sentence_template=item.sentence_template,
            explanation=item.explanation,
        )
        for item in items
    ]


# ── POST /v1/study/review ─────────────────────────────────────


@router.post("/v1/study/review", response_model=ReviewResponse)
async def submit_review(
    request: ReviewRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> ReviewResponse:
    now = datetime.now(UTC)
    user_id = current_user.user_id
    concept_id = request.concept_id

    # Fetch current progress — 404 if not started
    progress = await get_progress(conn, user_id=user_id, concept_id=concept_id)
    if progress is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No progress found for this concept. Start a session first.",
        )

    # Reconstruct FSRS card from DB
    card = reconstruct_card(
        fsrs_state=progress["fsrs_state"],
        fsrs_step=progress["fsrs_step"],
        fsrs_stability=progress["fsrs_stability"],
        fsrs_difficulty=progress["fsrs_difficulty"],
        fsrs_due=progress["fsrs_due"],
        fsrs_last_review=progress["fsrs_last_review"],
    )

    # Run FSRS scheduling
    rating = parse_rating(request.rating)
    review_result = process_review(card, rating, now)

    # Advance exercise difficulty
    old_difficulty = ExerciseType(progress["current_exercise_difficulty"])
    new_difficulty, new_streak = advance_difficulty(
        old_difficulty,
        progress["consecutive_correct"],
        request.correct,
    )
    difficulty_advanced = new_difficulty != old_difficulty

    # Apply prerequisite cap
    prereq_rows = await get_prerequisite_difficulties(
        conn, user_id=user_id, concept_id=concept_id,
    )
    prereq_types = [ExerciseType(r["current_exercise_difficulty"]) for r in prereq_rows]
    capped_difficulty = compute_capped_difficulty(new_difficulty, prereq_types)

    # Compute mastery
    was_mastered = bool(progress["is_mastered"])
    regressed = check_mastery_regression(was_mastered, request.correct)
    new_mastery = compute_mastery(
        current_difficulty=capped_difficulty,
        fsrs_stability=review_result.fsrs_stability,
        fsrs_state=review_result.fsrs_state,
    )
    is_mastered = new_mastery and not regressed
    mastery_changed = is_mastered != was_mastered

    # Persist progress + review
    await upsert_progress(
        conn,
        user_id=user_id,
        concept_id=concept_id,
        current_exercise_difficulty=capped_difficulty.value,
        consecutive_correct=new_streak,
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
        rating=request.rating,
        correct=request.correct,
        response=request.response,
        review_duration_ms=request.review_duration_ms,
    )
    await conn.commit()

    return ReviewResponse(
        concept_id=concept_id,
        new_exercise_difficulty=capped_difficulty,
        consecutive_correct=new_streak,
        is_mastered=is_mastered,
        fsrs_due=review_result.fsrs_due,
        difficulty_advanced=difficulty_advanced,
        mastery_changed=mastery_changed,
    )


# ── GET /v1/progress/{course_id} ──────────────────────────────


@router.get("/v1/progress/{course_id}", response_model=CourseProgressResponse)
async def get_course_progress(
    course_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> CourseProgressResponse:
    # Verify course exists
    course = await get_course(conn, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    rows = await get_progress_summary(
        conn, user_id=current_user.user_id, course_id=course_id,
    )
    levels = [
        CefrProgressItem(
            cefr_level=CefrLevel(row["cefr_level"]),
            total_concepts=row["total_concepts"],
            mastered_concepts=row["mastered_concepts"],
            mastery_percentage=round(
                row["mastered_concepts"] / row["total_concepts"] * 100, 1,
            ) if row["total_concepts"] > 0 else 0.0,
        )
        for row in rows
    ]
    return CourseProgressResponse(course_id=course_id, levels=levels)


# ── GET /v1/progress ──────────────────────────────────────────


@router.get("/v1/progress", response_model=AllProgressResponse)
async def get_all_progress(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> AllProgressResponse:
    """Return mastery progress for every course in a single query."""
    rows = await get_all_progress_summary(conn, user_id=current_user.user_id)

    courses_map: dict[UUID, list[CefrProgressItem]] = {}
    for row in rows:
        cid = row["course_id"]
        item = CefrProgressItem(
            cefr_level=CefrLevel(row["cefr_level"]),
            total_concepts=row["total_concepts"],
            mastered_concepts=row["mastered_concepts"],
            mastery_percentage=round(
                row["mastered_concepts"] / row["total_concepts"] * 100, 1,
            ) if row["total_concepts"] > 0 else 0.0,
        )
        courses_map.setdefault(cid, []).append(item)

    return AllProgressResponse(
        courses=[
            CourseProgressResponse(course_id=cid, levels=levels)
            for cid, levels in courses_map.items()
        ],
    )
