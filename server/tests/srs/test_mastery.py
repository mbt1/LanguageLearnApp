# SPDX-License-Identifier: Apache-2.0
"""Tests for mastery calculation logic."""
from __future__ import annotations

import pytest

from content.schemas import ExerciseType
from srs.mastery import check_mastery_regression, compute_mastery
from srs.scheduler import MASTERY_STABILITY_THRESHOLD


class TestComputeMastery:
    def test_all_criteria_met(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.forward_typing,
            reverse_difficulty=ExerciseType.reverse_typing,
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state="review",
        ) is True

    def test_stability_above_threshold(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.forward_typing,
            reverse_difficulty=ExerciseType.reverse_typing,
            fsrs_stability=MASTERY_STABILITY_THRESHOLD + 1.0,
            fsrs_state="review",
        ) is True

    def test_wrong_forward_difficulty_not_mastered(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.cloze,
            reverse_difficulty=ExerciseType.reverse_typing,
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state="review",
        ) is False

    def test_wrong_reverse_difficulty_not_mastered(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.forward_typing,
            reverse_difficulty=ExerciseType.reverse_mc,
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state="review",
        ) is False

    def test_wrong_state_not_mastered(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.forward_typing,
            reverse_difficulty=ExerciseType.reverse_typing,
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state="learning",
        ) is False

    def test_below_threshold_not_mastered(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.forward_typing,
            reverse_difficulty=ExerciseType.reverse_typing,
            fsrs_stability=MASTERY_STABILITY_THRESHOLD - 1.0,
            fsrs_state="review",
        ) is False

    def test_none_stability_not_mastered(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.forward_typing,
            reverse_difficulty=ExerciseType.reverse_typing,
            fsrs_stability=None,
            fsrs_state="review",
        ) is False

    def test_none_state_not_mastered(self) -> None:
        assert compute_mastery(
            forward_difficulty=ExerciseType.forward_typing,
            reverse_difficulty=ExerciseType.reverse_typing,
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state=None,
        ) is False

    @pytest.mark.parametrize("fwd,rev", [
        (ExerciseType.forward_mc, ExerciseType.reverse_typing),
        (ExerciseType.cloze, ExerciseType.reverse_typing),
        (ExerciseType.forward_typing, ExerciseType.reverse_mc),
        (ExerciseType.forward_typing, ExerciseType.reverse_cloze),
    ])
    def test_non_max_difficulties_not_mastered(self, fwd: ExerciseType, rev: ExerciseType) -> None:
        assert compute_mastery(
            forward_difficulty=fwd,
            reverse_difficulty=rev,
            fsrs_stability=1000.0,
            fsrs_state="review",
        ) is False


class TestCheckMasteryRegression:
    def test_was_mastered_and_wrong_regresses(self) -> None:
        assert check_mastery_regression(was_mastered=True, correct=False) is True

    def test_was_mastered_and_correct_no_regression(self) -> None:
        assert check_mastery_regression(was_mastered=True, correct=True) is False

    def test_not_mastered_wrong_no_regression(self) -> None:
        assert check_mastery_regression(was_mastered=False, correct=False) is False

    def test_not_mastered_correct_no_regression(self) -> None:
        assert check_mastery_regression(was_mastered=False, correct=True) is False
