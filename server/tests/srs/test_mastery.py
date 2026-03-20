# SPDX-License-Identifier: Apache-2.0
"""Tests for mastery calculation logic."""
from __future__ import annotations

from srs.mastery import check_mastery_regression, compute_mastery
from srs.scheduler import MASTERY_STABILITY_THRESHOLD


class TestComputeMastery:
    def test_all_criteria_met(self) -> None:
        assert compute_mastery(
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state="review",
        ) is True

    def test_stability_above_threshold(self) -> None:
        assert compute_mastery(
            fsrs_stability=MASTERY_STABILITY_THRESHOLD + 1.0,
            fsrs_state="review",
        ) is True

    def test_wrong_state_not_mastered(self) -> None:
        assert compute_mastery(
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state="learning",
        ) is False

    def test_relearning_state_not_mastered(self) -> None:
        assert compute_mastery(
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state="relearning",
        ) is False

    def test_below_threshold_not_mastered(self) -> None:
        assert compute_mastery(
            fsrs_stability=MASTERY_STABILITY_THRESHOLD - 1.0,
            fsrs_state="review",
        ) is False

    def test_none_stability_not_mastered(self) -> None:
        assert compute_mastery(
            fsrs_stability=None,
            fsrs_state="review",
        ) is False

    def test_none_state_not_mastered(self) -> None:
        assert compute_mastery(
            fsrs_stability=MASTERY_STABILITY_THRESHOLD,
            fsrs_state=None,
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
