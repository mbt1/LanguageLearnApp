# SPDX-License-Identifier: Apache-2.0
"""Grading provider interface and V1 exact-match implementation."""
from __future__ import annotations

from typing import Protocol

from grading.normalizer import normalize
from grading.schemas import GradingRequest, GradingResult, Verdict


class GradingProvider(Protocol):
    def grade(self, request: GradingRequest) -> GradingResult: ...


class ExactMatchGrader:
    """V1 grader: normalize both sides, then compare exact strings."""

    def grade(self, request: GradingRequest) -> GradingResult:
        norm_expected = normalize(request.correct_answer)
        norm_actual = normalize(request.user_answer)
        verdict = Verdict.accept if norm_expected == norm_actual else Verdict.reject
        return GradingResult(
            verdict=verdict,
            correct_answer=norm_expected,
            normalized_user_answer=norm_actual,
        )


#: Module-level singleton imported by route handlers.
default_grader: GradingProvider = ExactMatchGrader()
