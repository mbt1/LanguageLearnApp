# SPDX-License-Identifier: Apache-2.0
"""Tests for prerequisite difficulty cap logic."""
from __future__ import annotations

from content.schemas import ExerciseType
from srs.prerequisite_cap import compute_capped_difficulty


class TestComputeCappedDifficulty:
    def test_no_prerequisites_returns_current(self) -> None:
        result = compute_capped_difficulty(ExerciseType.typing, [])
        assert result == ExerciseType.typing

    def test_cap_to_lowest_prerequisite(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.typing,
            [ExerciseType.cloze, ExerciseType.reverse_typing],
        )
        assert result == ExerciseType.cloze

    def test_current_below_prerequisites_unchanged(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.multiple_choice,
            [ExerciseType.typing, ExerciseType.reverse_typing],
        )
        assert result == ExerciseType.multiple_choice

    def test_single_prerequisite_at_multiple_choice(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.reverse_typing,
            [ExerciseType.multiple_choice],
        )
        assert result == ExerciseType.multiple_choice

    def test_equal_to_prerequisites(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.cloze,
            [ExerciseType.cloze],
        )
        assert result == ExerciseType.cloze

    def test_multiple_prerequisites_all_at_max(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.typing,
            [ExerciseType.typing, ExerciseType.typing],
        )
        assert result == ExerciseType.typing

    def test_mixed_prerequisites_caps_to_min(self) -> None:
        result = compute_capped_difficulty(
            ExerciseType.typing,
            [ExerciseType.multiple_choice, ExerciseType.typing],
        )
        assert result == ExerciseType.multiple_choice
