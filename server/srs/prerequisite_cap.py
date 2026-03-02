# SPDX-License-Identifier: Apache-2.0
"""Prerequisite difficulty cap — pure Python, no DB imports."""
from __future__ import annotations

from content.schemas import ExerciseType  # noqa: TC001
from srs.difficulty import DIFFICULTY_INDEX, DIFFICULTY_ORDER


def compute_capped_difficulty(
    current_difficulty: ExerciseType,
    prerequisite_difficulties: list[ExerciseType],
) -> ExerciseType:
    """Cap a concept's difficulty to the minimum of its prerequisites.

    If there are no prerequisites, returns current_difficulty unchanged.
    """
    if not prerequisite_difficulties:
        return current_difficulty

    min_prereq_idx = min(DIFFICULTY_INDEX[d] for d in prerequisite_difficulties)
    current_idx = DIFFICULTY_INDEX[current_difficulty]
    return DIFFICULTY_ORDER[min(current_idx, min_prereq_idx)]
