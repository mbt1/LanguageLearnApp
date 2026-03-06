# SPDX-License-Identifier: Apache-2.0
"""Prerequisite difficulty cap — pure Python, no DB imports."""
from __future__ import annotations

from content.schemas import ExerciseType  # noqa: TC001
from srs.difficulty import (
    FORWARD_INDEX,
    FORWARD_ORDER,
    REVERSE_INDEX,
    REVERSE_ORDER,
    is_forward,
)


def compute_capped_difficulty(
    current_difficulty: ExerciseType,
    prerequisite_difficulties: list[ExerciseType],
) -> ExerciseType:
    """Cap a concept's difficulty to the minimum of its prerequisites.

    The cap applies within the same track (forward or reverse).
    If there are no prerequisites, returns current_difficulty unchanged.
    """
    if not prerequisite_difficulties:
        return current_difficulty

    if is_forward(current_difficulty):
        track_index = FORWARD_INDEX
        track_order = FORWARD_ORDER
    else:
        track_index = REVERSE_INDEX
        track_order = REVERSE_ORDER

    # Only consider prerequisites from the same track
    prereq_indices = [
        track_index[d] for d in prerequisite_difficulties if d in track_index
    ]
    if not prereq_indices:
        return current_difficulty

    min_prereq_idx = min(prereq_indices)
    current_idx = track_index[current_difficulty]
    return track_order[min(current_idx, min_prereq_idx)]
