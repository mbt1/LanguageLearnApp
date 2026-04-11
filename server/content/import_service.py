# SPDX-License-Identifier: Apache-2.0
"""Course import service — validates and persists a CourseImport payload."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection

from content.schemas import (
    ConceptImport,
    CourseImport,
    CourseImportResponse,
    ExerciseImport,
)
from db.queries.concepts import add_prerequisite, create_concept
from db.queries.courses import create_course
from db.queries.exercises import create_exercise, create_exercise_concept


def load_course_folder(folder: Path) -> CourseImport:
    """Load a folder-based course into a CourseImport model.

    Expected structure:
      folder/__course__.json  — course metadata (slug, title, languages)
      folder/*.json           — content files with {"concepts": [...]} and/or {"exercises": [...]}
    """
    meta_path = folder / "__course__.json"
    if not meta_path.exists():
        msg = f"Missing __course__.json in {folder}"
        raise ValueError(msg)

    meta: dict[str, Any] = json.loads(meta_path.read_text())

    all_concepts: list[ConceptImport] = []
    all_standalone_exercises: list[ExerciseImport] = []

    for path in sorted(folder.glob("*.json")):
        if path.name == "__course__.json":
            continue
        data: dict[str, Any] = json.loads(path.read_text())

        if "concepts" in data:
            all_concepts.extend(ConceptImport.model_validate(raw) for raw in data["concepts"])
        if "exercises" in data:
            all_standalone_exercises.extend(
                ExerciseImport.model_validate(raw) for raw in data["exercises"]
            )

    return CourseImport(
        slug=meta["slug"],
        title=meta["title"],
        source_language=meta["source_language"],
        target_language=meta["target_language"],
        concepts=all_concepts,
        standalone_exercises=all_standalone_exercises,
    )


async def import_course(
    conn: AsyncConnection,  # pyright: ignore[reportMissingTypeArgument]
    data: CourseImport,
) -> CourseImportResponse:
    """Validate and persist a course import.

    The caller controls the transaction — this function does not commit.
    Raises ValueError for validation failures (duplicate refs, unknown
    prerequisite refs, circular dependencies).
    """
    _validate_refs(data)
    order = _topological_sort(data)

    # Insert course
    course_row = await create_course(
        conn,
        slug=data.slug,
        title=data.title,
        source_language=data.source_language,
        target_language=data.target_language,
    )
    course_id: UUID = course_row["id"]

    # Build ref → ConceptImport lookup
    concept_by_ref = {c.ref: c for c in data.concepts}

    # Insert concepts in topological order, track ref → UUID
    ref_to_id: dict[str, UUID] = {}
    exercises_created = 0

    for ref in order:
        concept_data = concept_by_ref[ref]
        row = await create_concept(
            conn,
            course_id=course_id,
            ref=concept_data.ref,
            concept_type=concept_data.concept_type.value,
            cefr_level=concept_data.cefr_level.value,
            sequence=concept_data.sequence,
            explanation=concept_data.explanation,
        )
        concept_id_val: UUID = row["id"]
        ref_to_id[ref] = concept_id_val

        # Insert prerequisites
        if concept_data.prerequisites:
            for prereq_ref in concept_data.prerequisites:
                await add_prerequisite(
                    conn,
                    concept_id=concept_id_val,
                    prerequisite_id=ref_to_id[prereq_ref],
                    source="manual",
                )

        # Insert inline exercises (belong to this concept)
        for ex in concept_data.exercises:
            ex_row = await create_exercise(
                conn,
                exercise_type=ex.exercise_type,
                ref=ex.ref,
                reverse=ex.reverse,
                data=ex.data,
            )
            await create_exercise_concept(
                conn,
                exercise_id=ex_row["id"],
                concept_id=concept_id_val,
                is_primary=True,
            )
            exercises_created += 1

    # Insert standalone exercises (multi-concept)
    for ex in data.standalone_exercises:
        ex_row = await create_exercise(
            conn,
            exercise_type=ex.exercise_type,
            ref=ex.ref,
            reverse=ex.reverse,
            data=ex.data,
        )
        if ex.concept_refs:
            for i, cref in enumerate(ex.concept_refs):
                cid = ref_to_id.get(cref)
                if cid is None:
                    msg = f"Unknown concept ref '{cref}' in exercise '{ex.ref}'"
                    raise ValueError(msg)
                await create_exercise_concept(
                    conn,
                    exercise_id=ex_row["id"],
                    concept_id=cid,
                    is_primary=(i == 0),
                )
        exercises_created += 1

    return CourseImportResponse(
        course_id=course_id,
        concepts_created=len(data.concepts),
        exercises_created=exercises_created,
    )


def _validate_refs(data: CourseImport) -> None:
    """Check for duplicate refs and unknown prerequisite refs."""
    refs: set[str] = set()
    for concept in data.concepts:
        if concept.ref in refs:
            msg = f"Duplicate ref: '{concept.ref}'"
            raise ValueError(msg)
        refs.add(concept.ref)

    for concept in data.concepts:
        if concept.prerequisites:
            for prereq_ref in concept.prerequisites:
                if prereq_ref not in refs:
                    msg = f"Unknown prerequisite ref: '{prereq_ref}'"
                    raise ValueError(msg)


def _topological_sort(data: CourseImport) -> list[str]:
    """Return refs in topological order using Kahn's algorithm.

    Raises ValueError if a cycle is detected.
    """
    # Build adjacency and in-degree
    in_degree: dict[str, int] = {c.ref: 0 for c in data.concepts}
    dependents: dict[str, list[str]] = defaultdict(list)

    for concept in data.concepts:
        if concept.prerequisites:
            for prereq_ref in concept.prerequisites:
                dependents[prereq_ref].append(concept.ref)
                in_degree[concept.ref] += 1

    # Seed queue with nodes that have no prerequisites
    queue: deque[str] = deque(ref for ref, deg in in_degree.items() if deg == 0)
    order: list[str] = []

    while queue:
        ref = queue.popleft()
        order.append(ref)
        for dependent in dependents[ref]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(order) != len(data.concepts):
        remaining = {ref for ref, deg in in_degree.items() if deg > 0}
        msg = f"Circular dependency detected among: {remaining}"
        raise ValueError(msg)

    return order
