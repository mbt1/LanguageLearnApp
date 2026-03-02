# SPDX-License-Identifier: Apache-2.0
"""Exercise difficulty progression — pure Python, no DB imports."""
from __future__ import annotations

from content.schemas import ExerciseType

DIFFICULTY_ORDER: list[ExerciseType] = [
    ExerciseType.multiple_choice,
    ExerciseType.cloze,
    ExerciseType.reverse_typing,
    ExerciseType.typing,
]
CONSECUTIVE_CORRECT_TO_ADVANCE = 3

DIFFICULTY_INDEX: dict[ExerciseType, int] = {d: i for i, d in enumerate(DIFFICULTY_ORDER)}
_DIFFICULTY_INDEX = DIFFICULTY_INDEX  # internal alias


def advance_difficulty(
    current_difficulty: ExerciseType,
    consecutive_correct: int,
    correct: bool,  # noqa: FBT001
) -> tuple[ExerciseType, int]:
    """Compute new difficulty and streak after a review.

    Returns (new_difficulty, new_consecutive_correct).
    """
    if not correct:
        return current_difficulty, 0

    new_streak = consecutive_correct + 1
    idx = _DIFFICULTY_INDEX[current_difficulty]
    is_max = idx >= len(DIFFICULTY_ORDER) - 1

    if new_streak >= CONSECUTIVE_CORRECT_TO_ADVANCE and not is_max:
        return DIFFICULTY_ORDER[idx + 1], 0

    return current_difficulty, new_streak
