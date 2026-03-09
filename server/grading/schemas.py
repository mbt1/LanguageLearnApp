# SPDX-License-Identifier: Apache-2.0
"""Grading domain types — pure Python, no DB imports."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from content.schemas import ExerciseType  # noqa: TC001


class Verdict(StrEnum):
    accept = "accept"
    reject = "reject"
    partial = "partial"  # reserved for V2 ML partial-credit grading


@dataclass(frozen=True, slots=True)
class GradingRequest:
    exercise_type: ExerciseType
    correct_answers: list[str]
    user_answer: str
    language: str = field(default="default")  # hook for V2 language-specific normalizers


@dataclass(frozen=True, slots=True)
class GradingResult:
    verdict: Verdict
    correct_answer: str           # normalized form shown to user
    normalized_user_answer: str   # what was actually graded
