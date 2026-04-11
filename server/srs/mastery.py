# SPDX-License-Identifier: Apache-2.0
"""Mastery calculation — pure Python, no DB imports."""

from __future__ import annotations

from srs.scheduler import MASTERY_STABILITY_THRESHOLD


def compute_mastery(
    fsrs_stability: float | None,
    fsrs_state: str | None,
) -> bool:
    """Return True if all mastery criteria are satisfied.

    Mastery requires:
    - fsrs_state == "review"
    - fsrs_stability >= MASTERY_STABILITY_THRESHOLD (180 days)
    """
    if fsrs_state != "review":
        return False
    if fsrs_stability is None:
        return False
    return fsrs_stability >= MASTERY_STABILITY_THRESHOLD


def check_mastery_regression(was_mastered: bool, correct: bool) -> bool:  # noqa: FBT001
    """Return True if mastery should be revoked (was mastered + wrong answer)."""
    return was_mastered and not correct
