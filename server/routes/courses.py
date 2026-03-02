# SPDX-License-Identifier: Apache-2.0
"""Course and concept browsing / import endpoints."""
from __future__ import annotations

from collections import defaultdict
from typing import Annotated, Any
from uuid import UUID

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import AsyncConnection

from content.import_service import import_course
from content.schemas import (
    CefrLevel,
    ConceptDetail,
    ConceptSummary,
    ConceptType,
    CourseDetail,
    CourseImport,
    CourseImportResponse,
    CourseResponse,
    DependencySource,
    ExerciseResponse,
    ExerciseType,
    PrerequisiteInfo,
)
from db.pool import get_conn
from db.queries.concepts import (
    get_concept,
    get_prerequisites,
    list_concepts_by_course,
)
from db.queries.courses import get_course, list_courses
from db.queries.exercises import get_exercises_for_concept

router = APIRouter(tags=["courses"])


# ── Helpers ──────────────────────────────────────────────────


def _course_row_to_response(row: dict[str, Any]) -> CourseResponse:
    return CourseResponse(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        source_language=row["source_language"],
        target_language=row["target_language"],
        created_at=str(row["created_at"]),
    )


def _concept_row_to_summary(row: dict[str, Any]) -> ConceptSummary:
    return ConceptSummary(
        id=row["id"],
        concept_type=ConceptType(row["concept_type"]),
        cefr_level=CefrLevel(row["cefr_level"]),
        sequence=row["sequence"],
        prompt=row["prompt"],
        target=row["target"],
    )


# ── List courses ─────────────────────────────────────────────


@router.get("/v1/courses", response_model=list[CourseResponse])
async def list_courses_endpoint(
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> list[CourseResponse]:
    rows = await list_courses(conn)
    return [_course_row_to_response(r) for r in rows]


# ── Import course ────────────────────────────────────────────


@router.post(
    "/v1/courses/import",
    response_model=CourseImportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def import_course_endpoint(
    data: CourseImport,
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> CourseImportResponse:
    try:
        result = await import_course(conn, data)
        await conn.commit()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except psycopg.errors.UniqueViolation as exc:
        await conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A course with this slug already exists.",
        ) from exc
    return result


# ── Get course detail ────────────────────────────────────────


@router.get("/v1/courses/{course_id}", response_model=CourseDetail)
async def get_course_detail(
    course_id: UUID,
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> CourseDetail:
    course = await get_course(conn, course_id=course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    concepts = await list_concepts_by_course(conn, course_id=course_id)

    by_level: dict[CefrLevel, list[ConceptSummary]] = defaultdict(list)
    for row in concepts:
        level = CefrLevel(row["cefr_level"])
        by_level[level].append(_concept_row_to_summary(row))

    return CourseDetail(
        id=course["id"],
        slug=course["slug"],
        title=course["title"],
        source_language=course["source_language"],
        target_language=course["target_language"],
        created_at=str(course["created_at"]),
        concepts_by_level=dict(by_level),
    )


# ── List concepts by course ─────────────────────────────────


@router.get(
    "/v1/courses/{course_id}/concepts",
    response_model=list[ConceptSummary],
)
async def list_concepts_endpoint(
    course_id: UUID,
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
    cefr_level: Annotated[CefrLevel | None, Query()] = None,
) -> list[ConceptSummary]:
    rows = await list_concepts_by_course(
        conn,
        course_id=course_id,
        cefr_level=cefr_level.value if cefr_level else None,
    )
    return [_concept_row_to_summary(r) for r in rows]


# ── Get concept detail ───────────────────────────────────────


@router.get("/v1/concepts/{concept_id}", response_model=ConceptDetail)
async def get_concept_detail(
    concept_id: UUID,
    conn: Annotated[AsyncConnection, Depends(get_conn)],  # pyright: ignore[reportMissingTypeArgument]
) -> ConceptDetail:
    concept = await get_concept(conn, concept_id=concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")

    prereq_rows = await get_prerequisites(conn, concept_id=concept_id)
    exercise_rows = await get_exercises_for_concept(conn, concept_id=concept_id)

    return ConceptDetail(
        id=concept["id"],
        concept_type=ConceptType(concept["concept_type"]),
        cefr_level=CefrLevel(concept["cefr_level"]),
        sequence=concept["sequence"],
        prompt=concept["prompt"],
        target=concept["target"],
        explanation=concept["explanation"],
        prerequisites=[
            PrerequisiteInfo(
                concept_id=p["id"],
                prompt=p["prompt"],
                target=p["target"],
                cefr_level=CefrLevel(p["cefr_level"]),
                source=DependencySource(p["source"]),
            )
            for p in prereq_rows
        ],
        exercises=[
            ExerciseResponse(
                id=e["id"],
                exercise_type=ExerciseType(e["exercise_type"]),
                prompt=e["prompt"],
                correct_answer=e["correct_answer"],
                distractors=e["distractors"],
                sentence_template=e["sentence_template"],
            )
            for e in exercise_rows
        ],
    )
