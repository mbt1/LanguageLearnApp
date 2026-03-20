# SPDX-License-Identifier: Apache-2.0
"""Tests for the SRS session builder."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from content.schemas import CefrLevel, ConceptType
from srs.session import SessionItem, build_session

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_progress(
    concept_id: UUID | None = None,
    *,
    peak_difficulty: int = 10,
    fsrs_due: datetime | None = None,
    concept_type: str = "vocabulary",
    cefr_level: str = "A1",
    explanation: str | None = None,
) -> dict[str, Any]:
    """Build a fake due-review progress dict (as returned by list_due_reviews)."""
    return {
        "concept_id": concept_id or uuid4(),
        "peak_difficulty": peak_difficulty,
        "fsrs_due": fsrs_due or (NOW - timedelta(hours=1)),
        "concept_type": concept_type,
        "cefr_level": cefr_level,
        "fsrs_state": "review",
        "fsrs_step": None,
        "fsrs_stability": 30.0,
        "fsrs_difficulty": 5.0,
        "fsrs_last_review": NOW - timedelta(days=30),
        "is_mastered": False,
        "explanation": explanation,
    }


def _make_concept(
    concept_id: UUID | None = None,
    *,
    sequence: int = 1,
    cefr_level: str = "A1",
) -> dict[str, Any]:
    """Build a fake new concept dict (as returned by list_new_concepts)."""
    return {
        "id": concept_id or uuid4(),
        "course_id": uuid4(),
        "ref": f"concept-{sequence}",
        "concept_type": "vocabulary",
        "cefr_level": cefr_level,
        "sequence": sequence,
    }


# ── Session item dataclass ────────────────────────────────


class TestSessionItem:
    def test_is_review_field_preserved(self) -> None:
        item = SessionItem(
            concept_id=uuid4(),
            exercise_type="translate",
            difficulty=10,
            presentation="mc",
            is_review=True,
            concept_type=ConceptType.vocabulary,
            cefr_level=CefrLevel.A1,
        )
        assert item.is_review is True


# ── build_session ─────────────────────────────────────────


class TestBuildSession:
    def test_empty_inputs_returns_empty(self) -> None:
        result = build_session(
            due_reviews=[],
            new_concepts=[],
            all_active_progress=[],
            session_size=20,
        )
        assert result == []

    def test_due_reviews_come_first(self) -> None:
        review_id = uuid4()
        new_id = uuid4()
        result = build_session(
            due_reviews=[_make_progress(review_id)],
            new_concepts=[_make_concept(new_id)],
            all_active_progress=[_make_progress(review_id)],
            session_size=20,
        )
        # Review item comes first, then new concept
        assert result[0].concept_id == review_id
        assert result[1].concept_id == new_id

    def test_session_size_respected(self) -> None:
        reviews = [_make_progress() for _ in range(25)]
        result = build_session(
            due_reviews=reviews,
            new_concepts=[],
            all_active_progress=reviews,
            session_size=10,
        )
        assert len(result) <= 10

    def test_review_items_flagged_is_review(self) -> None:
        result = build_session(
            due_reviews=[_make_progress()],
            new_concepts=[],
            all_active_progress=[_make_progress()],
            session_size=20,
        )
        # Each review concept produces 1 item
        assert len(result) == 1
        assert result[0].is_review is True

    def test_new_concepts_flagged_not_is_review(self) -> None:
        result = build_session(
            due_reviews=[],
            new_concepts=[_make_concept()],
            all_active_progress=[],
            session_size=20,
        )
        # Each new concept produces 1 item
        assert len(result) == 1
        assert result[0].is_review is False

    def test_new_concepts_use_translate_mc_at_difficulty_10(self) -> None:
        result = build_session(
            due_reviews=[],
            new_concepts=[_make_concept()],
            all_active_progress=[],
            session_size=20,
        )
        assert len(result) == 1
        assert result[0].exercise_type == "translate"
        assert result[0].presentation == "mc"
        assert result[0].difficulty == 10

    def test_throttling_at_full_load_adds_no_new(self) -> None:
        # 20 items already active -> 100% load -> no new concepts
        active = [_make_progress() for _ in range(20)]
        new_concepts = [_make_concept()]
        result = build_session(
            due_reviews=[],
            new_concepts=new_concepts,
            all_active_progress=active,
            session_size=20,
        )
        assert len(result) == 0

    def test_no_throttling_when_empty(self) -> None:
        new_concepts = [_make_concept(sequence=i) for i in range(5)]
        result = build_session(
            due_reviews=[],
            new_concepts=new_concepts,
            all_active_progress=[],
            session_size=20,
        )
        # Each concept produces 1 item
        assert len(result) == 5

    def test_due_reviews_not_throttled(self) -> None:
        # Even at 100% active load, due reviews still come through
        active = [_make_progress() for _ in range(20)]
        due = active[:5]  # 5 are due right now
        result = build_session(
            due_reviews=due,
            new_concepts=[_make_concept()],
            all_active_progress=active,
            session_size=20,
        )
        # Each review concept produces 1 item; reviews always included; new may be throttled
        review_count = sum(1 for item in result if item.is_review)
        assert review_count == 5
