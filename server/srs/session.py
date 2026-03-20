# SPDX-License-Identifier: Apache-2.0
"""Study session builder — pure Python, no DB imports."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from content.schemas import CefrLevel, ConceptType
from srs.difficulty import derive_difficulty, difficulty_exercise_type, difficulty_presentation

# Throttle new concepts linearly from 80% load (max load = session_size).
_THROTTLE_START_RATIO = 0.8


@dataclass(frozen=True, slots=True)
class SessionItem:
    concept_id: UUID
    exercise_type: str          # translate / cloze / match
    difficulty: int             # 10 / 20 / 30 / ...
    presentation: str           # mc / arrange / typing
    is_review: bool
    concept_type: ConceptType
    cefr_level: CefrLevel
    exercise_id: UUID | None = field(default=None)
    reverse: bool = field(default=False)
    prompt: list[str] = field(default_factory=list)
    correct_answers: list[str] = field(default_factory=list)
    distractors: list[str] | None = field(default=None)
    explanation: str | None = field(default=None)


def _throttle_new_count(active_count: int, session_size: int, slots_remaining: int) -> int:
    """Compute how many new concepts to add given current load."""
    if session_size == 0:
        return 0
    load_ratio = active_count / session_size
    if load_ratio >= 1.0:
        return 0
    if load_ratio <= _THROTTLE_START_RATIO:
        return slots_remaining
    scale = 1.0 - (load_ratio - _THROTTLE_START_RATIO) / (1.0 - _THROTTLE_START_RATIO)
    return max(0, int(slots_remaining * scale))


def build_session(
    due_reviews: list[dict[str, Any]],
    new_concepts: list[dict[str, Any]],
    all_active_progress: list[dict[str, Any]],
    session_size: int,
) -> list[SessionItem]:
    """Build an ordered study session.

    Phase 1: Due reviews (priority), ordered by fsrs_due ascending.
    Phase 2: New concepts with predictive throttling.
    """
    items: list[SessionItem] = []

    # ── Phase 1: due reviews ──────────────────────────────
    sorted_reviews = sorted(due_reviews, key=lambda r: r["fsrs_due"])
    for row in sorted_reviews:
        if len(items) >= session_size:
            break
        difficulty = derive_difficulty(
            stability=row.get("fsrs_stability"),
            peak_difficulty=row.get("peak_difficulty", 10),
        )
        items.append(SessionItem(
            concept_id=row["concept_id"],
            exercise_type=difficulty_exercise_type(difficulty),
            difficulty=difficulty,
            presentation=difficulty_presentation(difficulty),
            is_review=True,
            concept_type=ConceptType(row["concept_type"]),
            cefr_level=CefrLevel(row["cefr_level"]),
            explanation=row.get("explanation"),
        ))

    # ── Phase 2: new concepts with throttling ─────────────
    slots_remaining = session_size - len(items)
    if slots_remaining > 0 and new_concepts:
        active_count = len(all_active_progress)
        allowed = _throttle_new_count(active_count, session_size, slots_remaining)
        concept_count = min(allowed, len(new_concepts)) if allowed > 0 else 0
        for concept in new_concepts[:concept_count]:
            if len(items) >= session_size:
                break
            items.append(SessionItem(
                concept_id=concept["id"],
                exercise_type=difficulty_exercise_type(10),
                difficulty=10,
                presentation=difficulty_presentation(10),
                is_review=False,
                concept_type=ConceptType(concept["concept_type"]),
                cefr_level=CefrLevel(concept["cefr_level"]),
                explanation=concept.get("explanation"),
            ))

    return items
