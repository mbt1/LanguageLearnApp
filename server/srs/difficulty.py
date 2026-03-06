# SPDX-License-Identifier: Apache-2.0
"""Exercise difficulty progression — pure Python, no DB imports.

Two independent tracks:
  Forward: forward_mc → cloze → forward_typing
  Reverse: reverse_mc → reverse_cloze → reverse_typing
"""
from __future__ import annotations

from content.schemas import FORWARD_TYPES, REVERSE_TYPES, ExerciseType

FORWARD_ORDER: list[ExerciseType] = [
    ExerciseType.forward_mc,
    ExerciseType.cloze,
    ExerciseType.forward_typing,
]
REVERSE_ORDER: list[ExerciseType] = [
    ExerciseType.reverse_mc,
    ExerciseType.reverse_cloze,
    ExerciseType.reverse_typing,
]

# Combined lookup for prerequisite cap (forward first, then reverse)
DIFFICULTY_ORDER: list[ExerciseType] = FORWARD_ORDER + REVERSE_ORDER

CONSECUTIVE_CORRECT_TO_ADVANCE = 3

FORWARD_INDEX: dict[ExerciseType, int] = {d: i for i, d in enumerate(FORWARD_ORDER)}
REVERSE_INDEX: dict[ExerciseType, int] = {d: i for i, d in enumerate(REVERSE_ORDER)}
# Unified index for prerequisite cap — maps all types to a linear position
DIFFICULTY_INDEX: dict[ExerciseType, int] = {d: i for i, d in enumerate(DIFFICULTY_ORDER)}
_DIFFICULTY_INDEX = DIFFICULTY_INDEX  # internal alias


def is_forward(exercise_type: ExerciseType) -> bool:
    """Return True if the exercise type belongs to the forward track."""
    return exercise_type in FORWARD_TYPES


def is_reverse(exercise_type: ExerciseType) -> bool:
    """Return True if the exercise type belongs to the reverse track."""
    return exercise_type in REVERSE_TYPES


def advance_difficulty(
    current_difficulty: ExerciseType,
    consecutive_correct: int,
    correct: bool,  # noqa: FBT001
) -> tuple[ExerciseType, int]:
    """Compute new difficulty and streak after a review within a single track.

    Returns (new_difficulty, new_consecutive_correct).
    """
    if not correct:
        return current_difficulty, 0

    if is_forward(current_difficulty):
        track_order = FORWARD_ORDER
        track_index = FORWARD_INDEX
    elif is_reverse(current_difficulty):
        track_order = REVERSE_ORDER
        track_index = REVERSE_INDEX
    else:
        return current_difficulty, consecutive_correct + 1

    new_streak = consecutive_correct + 1
    idx = track_index[current_difficulty]
    is_max = idx >= len(track_order) - 1

    if new_streak >= CONSECUTIVE_CORRECT_TO_ADVANCE and not is_max:
        return track_order[idx + 1], 0

    return current_difficulty, new_streak
