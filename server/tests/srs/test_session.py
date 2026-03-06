# SPDX-License-Identifier: Apache-2.0
"""Tests for the SRS session builder."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from content.schemas import CefrLevel, ConceptType, ExerciseType
from srs.session import SessionItem, build_session

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _make_progress(
    concept_id: UUID | None = None,
    *,
    forward_difficulty: str = "forward_mc",
    reverse_difficulty: str = "reverse_mc",
    fsrs_due: datetime | None = None,
    source_text: str = "hello",
    target_text: str = "hola",
    concept_type: str = "vocabulary",
    cefr_level: str = "A1",
) -> dict[str, Any]:
    """Build a fake due-review progress dict (as returned by list_due_reviews)."""
    return {
        "concept_id": concept_id or uuid4(),
        "forward_difficulty": forward_difficulty,
        "reverse_difficulty": reverse_difficulty,
        "forward_consecutive_correct": 0,
        "reverse_consecutive_correct": 0,
        "fsrs_due": fsrs_due or (NOW - timedelta(hours=1)),
        "source_text": source_text,
        "target_text": target_text,
        "concept_type": concept_type,
        "cefr_level": cefr_level,
        "fsrs_state": "review",
        "fsrs_step": None,
        "fsrs_stability": 30.0,
        "fsrs_difficulty": 5.0,
        "fsrs_last_review": NOW - timedelta(days=30),
        "is_mastered": False,
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
        "source_text": f"source-{sequence}",
        "target_text": f"target-{sequence}",
        "concept_type": "vocabulary",
        "cefr_level": cefr_level,
        "sequence": sequence,
    }


# ── Session item dataclass ────────────────────────────────


class TestSessionItem:
    def test_is_review_field_preserved(self) -> None:
        item = SessionItem(
            concept_id=uuid4(),
            exercise_type=ExerciseType.forward_mc,
            is_review=True,
            source_text="p",
            target_text="t",
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
            prereq_difficulties={},
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
            prereq_difficulties={},
            all_active_progress=[_make_progress(review_id)],
            session_size=20,
        )
        # Reviews produce 2 items (forward + reverse), then new concepts
        assert result[0].concept_id == review_id
        assert result[1].concept_id == review_id
        assert result[2].concept_id == new_id

    def test_session_size_respected(self) -> None:
        reviews = [_make_progress() for _ in range(25)]
        result = build_session(
            due_reviews=reviews,
            new_concepts=[],
            prereq_difficulties={},
            all_active_progress=reviews,
            session_size=10,
        )
        assert len(result) <= 10

    def test_review_items_flagged_is_review(self) -> None:
        result = build_session(
            due_reviews=[_make_progress()],
            new_concepts=[],
            prereq_difficulties={},
            all_active_progress=[_make_progress()],
            session_size=20,
        )
        # Each review concept produces 2 items (forward + reverse)
        assert len(result) == 2
        assert result[0].is_review is True
        assert result[1].is_review is True

    def test_new_concepts_flagged_not_is_review(self) -> None:
        result = build_session(
            due_reviews=[],
            new_concepts=[_make_concept()],
            prereq_difficulties={},
            all_active_progress=[],
            session_size=20,
        )
        # Each new concept produces 2 items (forward_mc + reverse_mc)
        assert len(result) == 2
        assert result[0].is_review is False
        assert result[1].is_review is False

    def test_new_concepts_use_forward_and_reverse_mc(self) -> None:
        result = build_session(
            due_reviews=[],
            new_concepts=[_make_concept()],
            prereq_difficulties={},
            all_active_progress=[],
            session_size=20,
        )
        assert result[0].exercise_type == ExerciseType.forward_mc
        assert result[1].exercise_type == ExerciseType.reverse_mc

    def test_prerequisite_cap_applied_to_reviews(self) -> None:
        review_id = uuid4()
        review = _make_progress(
            review_id,
            forward_difficulty="forward_typing",
            reverse_difficulty="reverse_typing",
        )
        result = build_session(
            due_reviews=[review],
            new_concepts=[],
            prereq_difficulties={
                review_id: [
                    {"forward_difficulty": "forward_mc", "reverse_difficulty": "reverse_mc"},
                ],
            },
            all_active_progress=[review],
            session_size=20,
        )
        # Forward item capped by forward prerequisite
        assert result[0].exercise_type == ExerciseType.forward_mc
        # Reverse item capped by reverse prerequisite
        assert result[1].exercise_type == ExerciseType.reverse_mc

    def test_throttling_at_full_load_adds_no_new(self) -> None:
        # 20 items already active → 100% load → no new concepts
        active = [_make_progress() for _ in range(20)]
        new_concepts = [_make_concept()]
        result = build_session(
            due_reviews=[],
            new_concepts=new_concepts,
            prereq_difficulties={},
            all_active_progress=active,
            session_size=20,
        )
        assert len(result) == 0

    def test_no_throttling_when_empty(self) -> None:
        new_concepts = [_make_concept(sequence=i) for i in range(5)]
        result = build_session(
            due_reviews=[],
            new_concepts=new_concepts,
            prereq_difficulties={},
            all_active_progress=[],
            session_size=20,
        )
        # Each concept produces 2 items (forward_mc + reverse_mc)
        assert len(result) == 10

    def test_due_reviews_not_throttled(self) -> None:
        # Even at 100% active load, due reviews still come through
        active = [_make_progress() for _ in range(20)]
        due = active[:5]  # 5 are due right now
        result = build_session(
            due_reviews=due,
            new_concepts=[_make_concept()],
            prereq_difficulties={},
            all_active_progress=active,
            session_size=20,
        )
        # Each review concept produces 2 items; reviews always included; new may be throttled
        review_count = sum(1 for item in result if item.is_review)
        assert review_count == 10  # 5 concepts * 2 items each
