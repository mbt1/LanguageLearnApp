# SPDX-License-Identifier: Apache-2.0
"""Tests for prerequisite difficulty cap logic."""
from __future__ import annotations

from content.schemas import ExerciseType
from srs.prerequisite_cap import compute_capped_difficulty


class TestComputeCappedDifficulty:
    def test_no_prerequisites_returns_current(self) -> None:
        result = compute_capped_difficulty(ExerciseType.forward_typing, [])
        assert result == ExerciseType.forward_typing

    def test_forward_cap_to_lowest_prerequisite(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.forward_typing,
            [ExerciseType.cloze, ExerciseType.forward_mc],
        )
        assert result == ExerciseType.forward_mc

    def test_forward_current_below_prerequisites_unchanged(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.forward_mc,
            [ExerciseType.forward_typing, ExerciseType.cloze],
        )
        assert result == ExerciseType.forward_mc

    def test_forward_single_prerequisite_at_forward_mc(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.cloze,
            [ExerciseType.forward_mc],
        )
        assert result == ExerciseType.forward_mc

    def test_forward_equal_to_prerequisites(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.cloze,
            [ExerciseType.cloze],
        )
        assert result == ExerciseType.cloze

    def test_forward_multiple_prerequisites_all_at_max(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.forward_typing,
            [ExerciseType.forward_typing, ExerciseType.forward_typing],
        )
        assert result == ExerciseType.forward_typing

    def test_forward_mixed_prerequisites_caps_to_min(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.forward_typing,
            [ExerciseType.forward_mc, ExerciseType.forward_typing],
        )
        assert result == ExerciseType.forward_mc

    def test_reverse_cap_to_lowest_prerequisite(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.reverse_typing,
            [ExerciseType.reverse_mc, ExerciseType.reverse_cloze],
        )
        assert result == ExerciseType.reverse_mc

    def test_reverse_current_below_prerequisites_unchanged(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.reverse_mc,
            [ExerciseType.reverse_typing],
        )
        assert result == ExerciseType.reverse_mc

    def test_cross_track_prerequisites_ignored(self) -> None:
        """Prerequisites from the other track are not considered for capping."""
        result = compute_capped_difficulty(
            ExerciseType.forward_typing,
            [ExerciseType.reverse_mc],  # different track, should be ignored
        )
        assert result == ExerciseType.forward_typing
