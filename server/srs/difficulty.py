# SPDX-License-Identifier: Apache-2.0
"""Difficulty derivation — pure Python, no DB imports.

Difficulty is derived from FSRS stability at serve time, not tracked as state.
A peak_difficulty floor prevents regression beyond one level (10 points).

Configuration is a sorted list of levels. Each level specifies:
  - level:          integer difficulty (multiples of 10 for future expansion)
  - exercise_type:  which content type to fetch (translate / cloze / match)
  - presentation:   how the client should render (mc / arrange / typing)
  - min_stability:  minimum FSRS stability (days) to unlock this level
"""
from __future__ import annotations

DIFFICULTY_CONFIG: list[dict] = [
    {"level": 10, "exercise_type": "translate", "presentation": "mc",      "min_stability": 0.0},
    {"level": 20, "exercise_type": "translate", "presentation": "arrange", "min_stability": 1.0},
    {"level": 30, "exercise_type": "cloze",     "presentation": "mc",      "min_stability": 3.0},
    {"level": 40, "exercise_type": "cloze",     "presentation": "typing",  "min_stability": 10.0},
    {"level": 50, "exercise_type": "translate",  "presentation": "typing",  "min_stability": 30.0},
]

MIN_DIFFICULTY = DIFFICULTY_CONFIG[0]["level"]
MAX_DIFFICULTY = DIFFICULTY_CONFIG[-1]["level"]
LEVEL_STEP = 10

# Pre-built lookup: level → config entry
_LEVEL_MAP: dict[int, dict] = {entry["level"]: entry for entry in DIFFICULTY_CONFIG}


def derive_difficulty(
    stability: float | None,
    peak_difficulty: int = MIN_DIFFICULTY,
) -> int:
    """Compute the current difficulty level from FSRS stability.

    The derived level is the highest level whose min_stability threshold
    is met.  A floor of ``peak_difficulty - LEVEL_STEP`` prevents the
    learner from regressing more than one level below their best.
    """
    if stability is None or stability <= 0:
        derived = MIN_DIFFICULTY
    else:
        derived = MIN_DIFFICULTY
        for entry in DIFFICULTY_CONFIG:
            if stability >= entry["min_stability"]:
                derived = entry["level"]
            else:
                break

    floor = max(MIN_DIFFICULTY, peak_difficulty - LEVEL_STEP)
    return max(derived, floor)


def difficulty_exercise_type(level: int) -> str:
    """Return the exercise_type string for a difficulty level."""
    entry = _LEVEL_MAP.get(level)
    if entry:
        return entry["exercise_type"]
    # Fall back to nearest level below
    for entry in reversed(DIFFICULTY_CONFIG):
        if entry["level"] <= level:
            return entry["exercise_type"]
    return DIFFICULTY_CONFIG[0]["exercise_type"]


def difficulty_presentation(level: int) -> str:
    """Return the presentation mode string for a difficulty level."""
    entry = _LEVEL_MAP.get(level)
    if entry:
        return entry["presentation"]
    for entry in reversed(DIFFICULTY_CONFIG):
        if entry["level"] <= level:
            return entry["presentation"]
    return DIFFICULTY_CONFIG[0]["presentation"]
