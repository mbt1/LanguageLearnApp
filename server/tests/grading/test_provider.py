# SPDX-License-Identifier: Apache-2.0
"""Tests for the grading provider."""
from __future__ import annotations

from content.schemas import ExerciseType
from grading.provider import ExactMatchGrader
from grading.schemas import GradingRequest, Verdict


def _req(
    user_answer: str,
    correct_answers: list[str] | None = None,
    exercise_type: ExerciseType = ExerciseType.forward_typing,
) -> GradingRequest:
    return GradingRequest(
        exercise_type=exercise_type,
        correct_answers=correct_answers or ["hola"],
        user_answer=user_answer,
    )


class TestExactMatchGrader:
    grader = ExactMatchGrader()

    def test_correct_answer_accepted(self) -> None:
        result = self.grader.grade(_req("hola"))
        assert result.verdict == Verdict.accept

    def test_wrong_answer_rejected(self) -> None:
        result = self.grader.grade(_req("adiós"))
        assert result.verdict == Verdict.reject

    def test_different_casing_accepted(self) -> None:
        result = self.grader.grade(_req("Hola"))
        assert result.verdict == Verdict.accept

    def test_extra_whitespace_accepted(self) -> None:
        result = self.grader.grade(_req("  hola  "))
        assert result.verdict == Verdict.accept

    def test_trailing_punctuation_accepted(self) -> None:
        result = self.grader.grade(_req("hola."))
        assert result.verdict == Verdict.accept

    def test_result_contains_normalized_forms(self) -> None:
        result = self.grader.grade(_req("Hola!"))
        assert result.correct_answer == "hola"
        assert result.normalized_user_answer == "hola"

    def test_multiple_choice_correct_option(self) -> None:
        result = self.grader.grade(
            _req("hola", exercise_type=ExerciseType.forward_mc),
        )
        assert result.verdict == Verdict.accept

    def test_multiple_choice_wrong_option(self) -> None:
        result = self.grader.grade(
            _req("adiós", exercise_type=ExerciseType.forward_mc),
        )
        assert result.verdict == Verdict.reject

    def test_cloze_correct_fill(self) -> None:
        result = self.grader.grade(
            _req("hola", exercise_type=ExerciseType.cloze),
        )
        assert result.verdict == Verdict.accept
