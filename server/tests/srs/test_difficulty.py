# SPDX-License-Identifier: Apache-2.0
"""Tests for exercise difficulty progression logic."""
from __future__ import annotations

import pytest

from content.schemas import ExerciseType
from srs.difficulty import (
    CONSECUTIVE_CORRECT_TO_ADVANCE,
    DIFFICULTY_ORDER,
    FORWARD_ORDER,
    REVERSE_ORDER,
    advance_difficulty,
)

# ── Constants ─────────────────────────────────────────────


class TestConstants:
    def test_forward_order(self) -> None:
        assert FORWARD_ORDER == [
            ExerciseType.forward_mc,
            ExerciseType.cloze,
            ExerciseType.forward_typing,
        ]

    def test_reverse_order(self) -> None:
        assert REVERSE_ORDER == [
            ExerciseType.reverse_mc,
            ExerciseType.reverse_cloze,
            ExerciseType.reverse_typing,
        ]

    def test_difficulty_order_is_forward_plus_reverse(self) -> None:
        assert DIFFICULTY_ORDER == FORWARD_ORDER + REVERSE_ORDER

    def test_consecutive_correct_to_advance(self) -> None:
        assert CONSECUTIVE_CORRECT_TO_ADVANCE == 3


# ── advance_difficulty (forward track) ───────────────────


class TestAdvanceDifficultyForward:
    def test_correct_increments_streak(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.forward_mc, consecutive_correct=0, correct=True,
        )
        assert new_diff == ExerciseType.forward_mc
        assert new_streak == 1

    def test_wrong_resets_streak(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.forward_mc, consecutive_correct=2, correct=False,
        )
        assert new_diff == ExerciseType.forward_mc
        assert new_streak == 0

    def test_advance_on_third_correct(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.forward_mc, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.cloze
        assert new_streak == 0

    def test_advance_cloze_to_forward_typing(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.cloze, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.forward_typing
        assert new_streak == 0

    def test_forward_typing_stays_at_max(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.forward_typing, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.forward_typing
        assert new_streak == 3  # keeps accumulating at max

    def test_wrong_at_forward_typing_resets_streak(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.forward_typing, consecutive_correct=5, correct=False,
        )
        assert new_diff == ExerciseType.forward_typing
        assert new_streak == 0

    def test_difficulty_never_decreases(self) -> None:
        new_diff, _ = advance_difficulty(
            ExerciseType.cloze, consecutive_correct=0, correct=False,
        )
        assert new_diff == ExerciseType.cloze


# ── advance_difficulty (reverse track) ───────────────────


class TestAdvanceDifficultyReverse:
    def test_advance_reverse_mc_to_reverse_cloze(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.reverse_mc, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.reverse_cloze
        assert new_streak == 0

    def test_advance_reverse_cloze_to_reverse_typing(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.reverse_cloze, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.reverse_typing
        assert new_streak == 0

    def test_reverse_typing_stays_at_max(self) -> None:
        new_diff, new_streak = advance_difficulty(
            ExerciseType.reverse_typing, consecutive_correct=2, correct=True,
        )
        assert new_diff == ExerciseType.reverse_typing
        assert new_streak == 3


# ── Parametric tests across all types ─────────────────────


class TestAdvanceDifficultyAllTypes:
    @pytest.mark.parametrize("difficulty", list(ExerciseType))
    def test_wrong_preserves_all_levels(self, difficulty: ExerciseType) -> None:
        new_diff, new_streak = advance_difficulty(difficulty, consecutive_correct=1, correct=False)
        assert new_diff == difficulty
        assert new_streak == 0
