# SPDX-License-Identifier: Apache-2.0
"""Study session builder — pure Python, no DB imports."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from content.schemas import CefrLevel, ConceptType, ExerciseType
from srs.prerequisite_cap import compute_capped_difficulty

# Throttle new concepts linearly from 80% load (max load = session_size).
_THROTTLE_START_RATIO = 0.8


@dataclass(frozen=True, slots=True)
class SessionItem:
    concept_id: UUID
    exercise_type: ExerciseType
    is_review: bool
    source_text: str
    target_text: str
    concept_type: ConceptType
    cefr_level: CefrLevel
    exercise_id: UUID | None = field(default=None)
    exercise_data: dict[str, Any] | None = field(default=None)
    correct_answer: str | None = field(default=None)
    distractors: list[str] | None = field(default=None)
    sentence_template: str | None = field(default=None)
    explanation: str | None = field(default=None)


def _capped_exercise_type(
    current_difficulty: str,
    concept_id: UUID,
    prereq_difficulties: dict[UUID, list[dict[str, Any]]],
    track: str,
) -> ExerciseType:
    """Apply prerequisite cap to a difficulty string, return ExerciseType."""
    prereq_rows = prereq_difficulties.get(concept_id, [])
    diff_key = "forward_difficulty" if track == "forward" else "reverse_difficulty"
    prereq_types = [ExerciseType(r[diff_key]) for r in prereq_rows]
    return compute_capped_difficulty(ExerciseType(current_difficulty), prereq_types)


def _throttle_new_count(active_count: int, session_size: int, slots_remaining: int) -> int:
    """Compute how many new concepts to add given current load."""
    if session_size == 0:
        return 0
    load_ratio = active_count / session_size
    if load_ratio >= 1.0:
        return 0
    if load_ratio <= _THROTTLE_START_RATIO:
        return slots_remaining
    # Linear reduction from full slots at 80% load to 0 at 100% load
    scale = 1.0 - (load_ratio - _THROTTLE_START_RATIO) / (1.0 - _THROTTLE_START_RATIO)
    return max(0, int(slots_remaining * scale))


def build_session(
    due_reviews: list[dict[str, Any]],
    new_concepts: list[dict[str, Any]],
    prereq_difficulties: dict[UUID, list[dict[str, Any]]],
    all_active_progress: list[dict[str, Any]],
    session_size: int,
) -> list[SessionItem]:
    """Build an ordered study session.

    Phase 1: Due reviews (priority), ordered by fsrs_due ascending.
              Each concept produces two items (forward + reverse track).
    Phase 2: New concepts with predictive throttling.
              Each new concept produces two items (forward_mc + reverse_mc).
    """
    items: list[SessionItem] = []

    # ── Phase 1: due reviews ──────────────────────────────
    sorted_reviews = sorted(due_reviews, key=lambda r: r["fsrs_due"])
    for row in sorted_reviews:
        if len(items) >= session_size:
            break
        cid = row["concept_id"]
        fwd_type = _capped_exercise_type(
            row["forward_difficulty"], cid, prereq_difficulties, "forward",
        )
        items.append(SessionItem(
            concept_id=cid,
            exercise_type=fwd_type,
            is_review=True,
            source_text=row["source_text"],
            target_text=row["target_text"],
            concept_type=ConceptType(row["concept_type"]),
            cefr_level=CefrLevel(row["cefr_level"]),
            explanation=row.get("explanation"),
        ))
        if len(items) >= session_size:
            break
        rev_type = _capped_exercise_type(
            row["reverse_difficulty"], cid, prereq_difficulties, "reverse",
        )
        items.append(SessionItem(
            concept_id=cid,
            exercise_type=rev_type,
            is_review=True,
            source_text=row["source_text"],
            target_text=row["target_text"],
            concept_type=ConceptType(row["concept_type"]),
            cefr_level=CefrLevel(row["cefr_level"]),
            explanation=row.get("explanation"),
        ))

    # ── Phase 2: new concepts with throttling ─────────────
    slots_remaining = session_size - len(items)
    if slots_remaining > 0 and new_concepts:
        active_count = len(all_active_progress)
        allowed = _throttle_new_count(active_count, session_size, slots_remaining)
        # Each new concept takes 2 slots (forward_mc + reverse_mc)
        concept_count = min(max(allowed // 2, 1) if allowed > 0 else 0, len(new_concepts))
        for concept in new_concepts[:concept_count]:
            if len(items) >= session_size:
                break
            items.append(SessionItem(
                concept_id=concept["id"],
                exercise_type=ExerciseType.forward_mc,
                is_review=False,
                source_text=concept["source_text"],
                target_text=concept["target_text"],
                concept_type=ConceptType(concept["concept_type"]),
                cefr_level=CefrLevel(concept["cefr_level"]),
                explanation=concept.get("explanation"),
            ))
            if len(items) >= session_size:
                break
            items.append(SessionItem(
                concept_id=concept["id"],
                exercise_type=ExerciseType.reverse_mc,
                is_review=False,
                source_text=concept["source_text"],
                target_text=concept["target_text"],
                concept_type=ConceptType(concept["concept_type"]),
                cefr_level=CefrLevel(concept["cefr_level"]),
                explanation=concept.get("explanation"),
            ))

    return items
