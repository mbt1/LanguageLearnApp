# SPDX-License-Identifier: Apache-2.0
"""Mastery calculation — pure Python, no DB imports."""
from __future__ import annotations

from content.schemas import ExerciseType
from srs.scheduler import MASTERY_STABILITY_THRESHOLD


def compute_mastery(
    forward_difficulty: ExerciseType | str,
    reverse_difficulty: ExerciseType | str,
    fsrs_stability: float | None,
    fsrs_state: str | None,
) -> bool:
    """Return True if all mastery criteria are satisfied.

    Mastery requires:
    - Forward track at forward_typing
    - Reverse track at reverse_typing
    - fsrs_state == "review"
    - fsrs_stability >= MASTERY_STABILITY_THRESHOLD (180 days)
    """
    if str(forward_difficulty) != ExerciseType.forward_typing:
        return False
    if str(reverse_difficulty) != ExerciseType.reverse_typing:
        return False
    if fsrs_state != "review":
        return False
    if fsrs_stability is None:
        return False
    return fsrs_stability >= MASTERY_STABILITY_THRESHOLD


def check_mastery_regression(was_mastered: bool, correct: bool) -> bool:  # noqa: FBT001
    """Return True if mastery should be revoked (was mastered + wrong answer)."""
    return was_mastered and not correct
