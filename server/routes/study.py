# SPDX-License-Identifier: Apache-2.0
"""Study session and review submission endpoints."""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import AsyncConnection

from auth.dependencies import get_current_user
from auth.schemas import CurrentUser  # noqa: TC001
from content.schemas import CefrLevel, ConceptType, ExerciseType
from db.pool import get_conn
from db.queries.concepts import get_concept
from db.queries.courses import get_course, list_courses
from db.queries.exercises import get_exercises_for_session
from db.queries.progress import (
    get_progress,
    list_all_active_progress,
    list_all_progress_detail,
    list_due_reviews,
    list_new_concepts,
    read_all_progress_summary,
    read_progress_summary,
    refresh_course_progress_summary,
    refresh_progress_summary,
    upsert_progress,
)
from db.queries.reviews import record_review
from srs.difficulty import derive_difficulty, difficulty_exercise_type, difficulty_presentation
from srs.mastery import check_mastery_regression, compute_mastery
from srs.scheduler import (
    parse_rating,
    process_review,
    reconstruct_card,
)
from srs.schemas import (
    AllProgressResponse,
    CefrProgressItem,
    ConceptProgressDetail,
    CourseProgressResponse,
    ReviewRequest,
    ReviewResponse,
    ReviewScheduleResponse,
    StudySessionItem,
    StudySessionRequest,
    StudySessionResponse,
)
from srs.session import SessionItem, build_session

router = APIRouter(tags=["study"])

# Number of distractors to select from pools for MC/cloze exercises.
_NUM_DISTRACTORS = 3


# ── POST /v1/study/session ────────────────────────────────────


@router.post("/v1/study/session", response_model=StudySessionResponse)
async def create_study_session(  # noqa: C901, PLR0912
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

    due_reviews: list[dict[str, Any]] = []
    if request.concept_ids is not None:
        # ── Targeted session: specific concepts only ──
        if len(request.concept_ids) > request.session_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many concept_ids for session_size",
            )
        items: list[SessionItem] = []
        for cid in request.concept_ids:
            concept = await get_concept(conn, concept_id=cid)
            if concept is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Concept {cid} not found",
                )
            if concept["course_id"] != course_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Concept {cid} does not belong to course",
                )
            progress = await get_progress(conn, user_id=user_id, concept_id=cid)
            if progress:
                difficulty = derive_difficulty(
                    stability=progress.get("fsrs_stability"),
                    peak_difficulty=progress.get("peak_difficulty", 10),
                )
            else:
                difficulty = 10
            items.append(
                SessionItem(
                    concept_id=cid,
                    exercise_type=difficulty_exercise_type(difficulty),
                    difficulty=difficulty,
                    presentation=difficulty_presentation(difficulty),
                    is_review=progress is not None,
                    concept_type=ConceptType(concept["concept_type"]),
                    cefr_level=CefrLevel(concept["cefr_level"]),
                    explanation=concept.get("explanation"),
                )
            )
    else:
        # ── Normal session: algorithmic selection ──
        due_reviews = await list_due_reviews(
            conn,
            user_id=user_id,
            now=now,
            limit=request.session_size,
        )
        new_concepts = await list_new_concepts(
            conn,
            user_id=user_id,
            course_id=course_id,
            limit=request.session_size,
        )
        all_active = await list_all_active_progress(conn, user_id=user_id, course_id=course_id)

        items = build_session(
            due_reviews=due_reviews,
            new_concepts=new_concepts,
            all_active_progress=all_active,
            session_size=request.session_size,
        )

    # Batch fetch exercise-specific data from JSONB
    exercise_keys = [(item.concept_id, item.exercise_type) for item in items]
    exercise_map = await get_exercises_for_session(conn, items=exercise_keys)
    enriched_items: list[SessionItem] = []
    for item in items:
        exercises = exercise_map.get((item.concept_id, item.exercise_type))
        if exercises:
            ex = random.choice(exercises)  # noqa: S311
            enriched_items.append(_enrich_item(item, ex))
        else:
            enriched_items.append(item)
    items = enriched_items

    # Create initial progress rows for new concepts added to session
    new_concept_ids_seen: set[UUID] = set()
    new_items = [item for item in items if not item.is_review]
    for item in new_items:
        if item.concept_id not in new_concept_ids_seen:
            new_concept_ids_seen.add(item.concept_id)
            await upsert_progress(
                conn,
                user_id=user_id,
                concept_id=item.concept_id,
                fsrs_due=now,
            )

    # Refresh progress summary cache (new concepts change "not_started" counts)
    if new_items:
        await refresh_course_progress_summary(
            conn,
            user_id=user_id,
            course_id=course_id,
        )
    await conn.commit()

    review_count = (
        sum(1 for i in items if i.is_review)
        if request.concept_ids is not None
        else len(due_reviews)
    )
    return StudySessionResponse(
        items=_items_to_response(items),
        total_due_reviews=review_count,
        new_concepts_added=len(new_items),
    )


def _row_to_progress_item(row: dict[str, Any]) -> CefrProgressItem:
    return CefrProgressItem(
        cefr_level=CefrLevel(row["cefr_level"]),
        total_concepts=row["total_concepts"],
        not_started=row["not_started"],
        seen=row["seen"],
        familiar=row["familiar"],
        practiced=row["practiced"],
        proficient=row["proficient"],
        mastered=row["mastered"],
    )


def _select_distractors(
    distractor_pools: dict[str, list[str]],
    n: int = _NUM_DISTRACTORS,
) -> list[str]:
    """Select N distractors from typed distractor pools.

    Flattens all pools, deduplicates, shuffles, and picks up to N.
    """
    all_distractors: list[str] = []
    seen: set[str] = set()
    for pool in distractor_pools.values():
        for d in pool:
            if d not in seen:
                seen.add(d)
                all_distractors.append(d)
    random.shuffle(all_distractors)
    return all_distractors[:n]


def _enrich_item(item: SessionItem, ex: dict[str, Any]) -> SessionItem:
    """Enrich a session item from a JSONB exercise row."""
    data: dict[str, Any] = ex.get("data") or {}

    # New format: prompt is array, answers is array of arrays
    prompt: list[str] = data.get("prompt", [])
    if isinstance(prompt, str):
        prompt = [prompt]
    answers: list[list[str]] = data.get("answers", [[]])
    # Flatten alternatives for the first position
    correct_answers: list[str] = answers[0] if answers else []
    if correct_answers and isinstance(correct_answers, str):
        correct_answers = [correct_answers]

    # Select distractors for MC/cloze exercises
    distractors: list[str] | None = None
    raw_distractors: dict[str, list[str]] | None = data.get("distractors")
    if raw_distractors:
        selected = _select_distractors(raw_distractors)
        answer_set = set(correct_answers)
        selected = [d for d in selected if d not in answer_set]
        distractors = selected[:_NUM_DISTRACTORS] if selected else None

    return replace(
        item,
        exercise_id=ex["id"],
        reverse=ex.get("reverse", False),
        prompt=prompt,
        correct_answers=correct_answers,
        distractors=distractors,
    )


def _items_to_response(items: list[SessionItem]) -> list[StudySessionItem]:
    return [
        StudySessionItem(
            concept_id=item.concept_id,
            exercise_type=ExerciseType(item.exercise_type),
            difficulty=item.difficulty,
            presentation=item.presentation,
            reverse=item.reverse,
            is_review=item.is_review,
            concept_type=item.concept_type,
            cefr_level=item.cefr_level,
            exercise_id=item.exercise_id,
            prompt=item.prompt,
            correct_answers=item.correct_answers,
            distractors=item.distractors,
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

    # Update peak difficulty on correct answer
    old_peak = progress["peak_difficulty"]
    new_peak = max(old_peak, request.difficulty) if request.correct else old_peak

    # Compute mastery
    was_mastered = bool(progress["is_mastered"])
    regressed = check_mastery_regression(was_mastered, request.correct)
    new_mastery = compute_mastery(
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
        rating=request.rating,
        correct=request.correct,
        response=request.response,
        review_duration_ms=request.review_duration_ms,
    )

    # Refresh progress summary cache
    concept = await get_concept(conn, concept_id=concept_id)
    if concept:
        await refresh_progress_summary(
            conn,
            user_id=user_id,
            course_id=concept["course_id"],
            cefr_level=concept["cefr_level"],
        )
    await conn.commit()

    return ReviewResponse(
        concept_id=concept_id,
        difficulty=derive_difficulty(
            stability=review_result.fsrs_stability,
            peak_difficulty=new_peak,
        ),
        peak_difficulty=new_peak,
        is_mastered=is_mastered,
        fsrs_due=review_result.fsrs_due,
        mastery_changed=mastery_changed,
    )


# ── GET /v1/progress/{course_id} ──────────────────────────────


@router.get("/v1/progress/{course_id}", response_model=CourseProgressResponse)
async def get_course_progress(
    course_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> CourseProgressResponse:
    course = await get_course(conn, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    rows = await read_progress_summary(
        conn,
        user_id=current_user.user_id,
        course_id=course_id,
    )
    if not rows:
        await refresh_course_progress_summary(
            conn,
            user_id=current_user.user_id,
            course_id=course_id,
        )
        await conn.commit()
        rows = await read_progress_summary(
            conn,
            user_id=current_user.user_id,
            course_id=course_id,
        )
    levels = [_row_to_progress_item(row) for row in rows]
    return CourseProgressResponse(course_id=course_id, levels=levels)


# ── GET /v1/progress ──────────────────────────────────────────


@router.get("/v1/progress", response_model=AllProgressResponse)
async def get_all_progress(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> AllProgressResponse:
    """Return progress for every course from precalculated cache."""
    rows = await read_all_progress_summary(conn, user_id=current_user.user_id)

    if not rows:
        all_courses = await list_courses(conn)
        for c in all_courses:
            await refresh_course_progress_summary(
                conn,
                user_id=current_user.user_id,
                course_id=c["id"],
            )
        await conn.commit()
        rows = await read_all_progress_summary(conn, user_id=current_user.user_id)

    courses_map: dict[UUID, list[CefrProgressItem]] = {}
    for row in rows:
        cid = row["course_id"]
        courses_map.setdefault(cid, []).append(_row_to_progress_item(row))

    return AllProgressResponse(
        courses=[
            CourseProgressResponse(course_id=cid, levels=levels)
            for cid, levels in courses_map.items()
        ],
    )


# ── GET /v1/review-schedule/{course_id} ──────────────────


@router.get("/v1/review-schedule/{course_id}", response_model=ReviewScheduleResponse)
async def get_review_schedule(
    course_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> ReviewScheduleResponse:
    """Return full SRS detail for all concepts in a course."""
    course = await get_course(conn, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

    rows = await list_all_progress_detail(
        conn,
        user_id=current_user.user_id,
        course_id=course_id,
    )
    items = [
        ConceptProgressDetail(
            concept_id=row["concept_id"],
            ref=row["ref"],
            concept_type=row["concept_type"],
            cefr_level=row["cefr_level"],
            peak_difficulty=row["peak_difficulty"],
            is_mastered=row["is_mastered"],
            fsrs_state=row["fsrs_state"],
            fsrs_stability=row["fsrs_stability"],
            fsrs_difficulty=row["fsrs_difficulty"],
            fsrs_due=row["fsrs_due"],
            fsrs_last_review=row["fsrs_last_review"],
        )
        for row in rows
    ]
    return ReviewScheduleResponse(course_id=course_id, items=items)
