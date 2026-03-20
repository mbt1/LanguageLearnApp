# SPDX-License-Identifier: Apache-2.0
"""Tests for derived difficulty logic."""
from __future__ import annotations

from srs.difficulty import (
    DIFFICULTY_CONFIG,
    LEVEL_STEP,
    MAX_DIFFICULTY,
    MIN_DIFFICULTY,
    derive_difficulty,
    difficulty_exercise_type,
    difficulty_presentation,
)


# ── derive_difficulty ────────────────────────────────────


class TestDeriveDifficulty:
    def test_none_stability_returns_min(self) -> None:
        assert derive_difficulty(stability=None) == MIN_DIFFICULTY

    def test_zero_stability_returns_min(self) -> None:
        assert derive_difficulty(stability=0.0) == MIN_DIFFICULTY

    def test_negative_stability_returns_min(self) -> None:
        assert derive_difficulty(stability=-1.0) == MIN_DIFFICULTY

    def test_low_stability_returns_level_10(self) -> None:
        assert derive_difficulty(stability=0.5) == 10

    def test_stability_1_returns_level_20(self) -> None:
        assert derive_difficulty(stability=1.0) == 20

    def test_stability_3_returns_level_30(self) -> None:
        assert derive_difficulty(stability=3.0) == 30

    def test_stability_10_returns_level_40(self) -> None:
        assert derive_difficulty(stability=10.0) == 40

    def test_stability_30_returns_level_50(self) -> None:
        assert derive_difficulty(stability=30.0) == 50

    def test_high_stability_caps_at_max(self) -> None:
        assert derive_difficulty(stability=1000.0) == MAX_DIFFICULTY

    def test_peak_floor_prevents_deep_regression(self) -> None:
        # Peak was 50, stability dropped to 0 → floor is 50-10=40
        assert derive_difficulty(stability=0.0, peak_difficulty=50) == 40

    def test_peak_floor_allows_one_step_regression(self) -> None:
        # Peak 30, stability 0 → floor is 20
        assert derive_difficulty(stability=0.0, peak_difficulty=30) == 20

    def test_peak_floor_at_min_does_not_go_below_min(self) -> None:
        assert derive_difficulty(stability=0.0, peak_difficulty=MIN_DIFFICULTY) == MIN_DIFFICULTY

    def test_derived_above_floor_uses_derived(self) -> None:
        # Peak 20, stability gives level 30 → use 30
        assert derive_difficulty(stability=3.0, peak_difficulty=20) == 30


# ── difficulty_exercise_type ─────────────────────────────


class TestDifficultyExerciseType:
    def test_level_10_translate(self) -> None:
        assert difficulty_exercise_type(10) == "translate"

    def test_level_30_cloze(self) -> None:
        assert difficulty_exercise_type(30) == "cloze"

    def test_level_50_translate(self) -> None:
        assert difficulty_exercise_type(50) == "translate"

    def test_all_config_levels_resolve(self) -> None:
        for entry in DIFFICULTY_CONFIG:
            assert difficulty_exercise_type(entry["level"]) == entry["exercise_type"]


# ── difficulty_presentation ──────────────────────────────


class TestDifficultyPresentation:
    def test_level_10_mc(self) -> None:
        assert difficulty_presentation(10) == "mc"

    def test_level_20_arrange(self) -> None:
        assert difficulty_presentation(20) == "arrange"

    def test_level_50_typing(self) -> None:
        assert difficulty_presentation(50) == "typing"

    def test_all_config_levels_resolve(self) -> None:
        for entry in DIFFICULTY_CONFIG:
            assert difficulty_presentation(entry["level"]) == entry["presentation"]


# ── Constants ────────────────────────────────────────────


class TestConstants:
    def test_min_difficulty(self) -> None:
        assert MIN_DIFFICULTY == 10

    def test_max_difficulty(self) -> None:
        assert MAX_DIFFICULTY == 50

    def test_level_step(self) -> None:
        assert LEVEL_STEP == 10

    def test_config_sorted_by_level(self) -> None:
        levels = [e["level"] for e in DIFFICULTY_CONFIG]
        assert levels == sorted(levels)
