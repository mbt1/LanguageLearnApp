# SPDX-License-Identifier: Apache-2.0
"""Tests for exercise difficulty progression logic."""
from __future__ import annotations

import pytest

from content.schemas import ExerciseType
from srs.difficulty import (
    CONSECUTIVE_CORRECT_TO_ADVANCE,
    DIFFICULTY_ORDER,
    advance_difficulty,
)

# ── Constants ─────────────────────────────────────────────


class TestConstants:
    def test_difficulty_order(self) -> None:
        assert DIFFICULTY_ORDER == [
            ExerciseType.multiple_choice,
            ExerciseType.cloze,
            ExerciseType.reverse_typing,
            ExerciseType.typing,
        ]

    def test_consecutive_correct_to_advance(self) -> None:
        assert CONSECUTIVE_CORRECT_TO_ADVANCE == 3


# ── advance_difficulty ────────────────────────────────────


class TestAdvanceDifficulty:
    def test_correct_increments_streak(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.multiple_choice, consecutive_correct=0, correct=True,
        )
        assert new_diff == ExerciseType.multiple_choice
        assert new_streak == 1

    def test_wrong_resets_streak(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.multiple_choice, consecutive_correct=2, correct=False,
        )
        assert new_diff == ExerciseType.multiple_choice
        assert new_streak == 0

    def test_advance_on_third_correct(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.multiple_choice, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.cloze
        assert new_streak == 0

    def test_advance_cloze_to_reverse_typing(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.cloze, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.reverse_typing
        assert new_streak == 0

    def test_advance_reverse_typing_to_typing(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.reverse_typing, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.typing
        assert new_streak == 0

    def test_typing_stays_at_max(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.typing, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.typing
        assert new_streak == 3  # keeps accumulating at max

    def test_wrong_at_typing_resets_streak(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.typing, consecutive_correct=5, correct=False,
        )
        assert new_diff == ExerciseType.typing
        assert new_streak == 0

    def test_difficulty_never_decreases(self) -> None:
        new_diff, _ = advance_difficulty(
            ExerciseType.cloze, consecutive_correct=0, correct=False,
        )
        assert new_diff == ExerciseType.cloze

    @pytest.mark.parametrize("difficulty", list(ExerciseType))
    def test_wrong_preserves_all_levels(self, difficulty: ExerciseType) -> None:
        new_diff, new_streak = advance_difficulty(difficulty, consecutive_correct=1, correct=False)
        assert new_diff == difficulty
        assert new_streak == 0
