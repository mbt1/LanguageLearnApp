# SPDX-License-Identifier: Apache-2.0
"""Grading provider interface and V1 exact-match implementation."""

from __future__ import annotations

from typing import Protocol

from grading.normalizer import normalize
from grading.schemas import GradingRequest, GradingResult, Verdict


class GradingProvider(Protocol):
    def grade(self, request: GradingRequest) -> GradingResult: ...


class ExactMatchGrader:
    """V1 grader: normalize both sides, accept if any correct answer matches."""

    def grade(self, request: GradingRequest) -> GradingResult:
        norm_actual = normalize(request.user_answer)
        # Primary answer (first target) shown to user in feedback
        primary = normalize(request.correct_answers[0]) if request.correct_answers else ""
        # Check against all accepted answers
        verdict = Verdict.reject
        for answer in request.correct_answers:
            if normalize(answer) == norm_actual:
                verdict = Verdict.accept
                break
        return GradingResult(
            verdict=verdict,
            correct_answer=primary,
            normalized_user_answer=norm_actual,
        )


#: Module-level singleton imported by route handlers.
default_grader: GradingProvider = ExactMatchGrader()
