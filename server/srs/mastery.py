# SPDX-License-Identifier: Apache-2.0
"""Mastery calculation — pure Python, no DB imports."""
from __future__ import annotations

from content.schemas import ExerciseType
from srs.scheduler import MASTERY_STABILITY_THRESHOLD


def compute_mastery(
    current_difficulty: ExerciseType,
    fsrs_stability: float | None,
    fsrs_state: str | None,
) -> bool:
    """Return True if all mastery criteria are satisfied.

    Mastery requires:
    - Difficulty at typing level
    - fsrs_state == "Review"
    - fsrs_stability >= MASTERY_STABILITY_THRESHOLD (180 days)
    """
    if current_difficulty != ExerciseType.typing:
        return False
    if fsrs_state != "review":
        return False
    if fsrs_stability is None:
        return False
    return fsrs_stability >= MASTERY_STABILITY_THRESHOLD


def check_mastery_regression(was_mastered: bool, correct: bool) -> bool:  # noqa: FBT001
    """Return True if mastery should be revoked (was mastered + wrong answer)."""
    return was_mastered and not correct
