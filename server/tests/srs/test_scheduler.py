# SPDX-License-Identifier: Apache-2.0
"""Tests for SRS scheduler wrapper around the fsrs library."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fsrs import Rating, State

from srs.scheduler import (
    DESIRED_RETENTION,
    MASTERY_STABILITY_THRESHOLD,
    ReviewResult,
    create_new_card,
    parse_rating,
    process_review,
    reconstruct_card,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


# ── Constants ─────────────────────────────────────────────


class TestConstants:
    def test_desired_retention(self) -> None:
        assert DESIRED_RETENTION == 0.9

    def test_mastery_stability_threshold(self) -> None:
        assert MASTERY_STABILITY_THRESHOLD == 180.0


# ── create_new_card ───────────────────────────────────────


class TestCreateNewCard:
    def test_returns_learning_state(self) -> None:
        card = create_new_card(NOW)
        assert card.state == State.Learning
        assert card.step == 0
        assert card.stability is None
        assert card.difficulty is None

    def test_due_is_now(self) -> None:
        card = create_new_card(NOW)
        assert card.due == NOW


# ── reconstruct_card ─────────────────────────────────────


class TestReconstructCard:
    def test_from_none_returns_fresh_card(self) -> None:
        card = reconstruct_card(
            fsrs_state=None,
            fsrs_step=None,
            fsrs_stability=None,
            fsrs_difficulty=None,
            fsrs_due=None,
            fsrs_last_review=None,
        )
        assert card.state == State.Learning
        assert card.step == 0

    def test_from_learning_state(self) -> None:
        card = reconstruct_card(
            fsrs_state="learning",
            fsrs_step=1,
            fsrs_stability=2.3,
            fsrs_difficulty=2.1,
            fsrs_due=NOW,
            fsrs_last_review=NOW,
        )
        assert card.state == State.Learning
        assert card.step == 1
        assert card.stability == 2.3
        assert card.difficulty == 2.1

    def test_from_review_state(self) -> None:
        card = reconstruct_card(
            fsrs_state="review",
            fsrs_step=None,
            fsrs_stability=30.0,
            fsrs_difficulty=5.0,
            fsrs_due=NOW,
            fsrs_last_review=NOW,
        )
        assert card.state == State.Review

    def test_from_relearning_state(self) -> None:
        card = reconstruct_card(
            fsrs_state="relearning",
            fsrs_step=0,
            fsrs_stability=10.0,
            fsrs_difficulty=5.0,
            fsrs_due=NOW,
            fsrs_last_review=NOW,
        )
        assert card.state == State.Relearning


# ── parse_rating ──────────────────────────────────────────


class TestParseRating:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("again", Rating.Again),
            ("hard", Rating.Hard),
            ("good", Rating.Good),
            ("easy", Rating.Easy),
        ],
    )
    def test_valid_ratings(self, text: str, expected: Rating) -> None:
        assert parse_rating(text) == expected

    def test_invalid_rating_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown rating"):
            parse_rating("perfect")


# ── process_review ────────────────────────────────────────


class TestProcessReview:
    def test_returns_review_result(self) -> None:
        card = create_new_card(NOW)
        result = process_review(card, Rating.Good, NOW)
        assert isinstance(result, ReviewResult)

    def test_fields_populated(self) -> None:
        card = create_new_card(NOW)
        result = process_review(card, Rating.Good, NOW)
        assert result.fsrs_state is not None
        assert result.fsrs_due is not None
        assert result.fsrs_last_review == NOW

    @pytest.mark.parametrize("rating", list(Rating))
    def test_all_ratings(self, rating: Rating) -> None:
        card = create_new_card(NOW)
        result = process_review(card, rating, NOW)
        assert result.fsrs_state in {"learning", "review", "relearning"}

    def test_stability_grows_over_time(self) -> None:
        card = create_new_card(NOW)
        # First review
        r1 = process_review(card, Rating.Good, NOW)
        card2 = reconstruct_card(
            fsrs_state=r1.fsrs_state,
            fsrs_step=r1.fsrs_step,
            fsrs_stability=r1.fsrs_stability,
            fsrs_difficulty=r1.fsrs_difficulty,
            fsrs_due=r1.fsrs_due,
            fsrs_last_review=r1.fsrs_last_review,
        )
        # Second review at due time
        assert r1.fsrs_due is not None
        r2 = process_review(card2, Rating.Good, r1.fsrs_due)
        # After transitioning to Review, stability should be set
        if r2.fsrs_stability is not None and r1.fsrs_stability is not None:
            assert r2.fsrs_stability >= r1.fsrs_stability

    def test_again_rating_keeps_low_step(self) -> None:
        card = create_new_card(NOW)
        result = process_review(card, Rating.Again, NOW)
        # Again on a new card should keep it in Learning with step 0
        assert result.fsrs_state == "learning"
        assert result.fsrs_step == 0

    def test_fuzzing_disabled_by_default(self) -> None:
        card = create_new_card(NOW)
        r1 = process_review(card, Rating.Good, NOW)
        r2 = process_review(card, Rating.Good, NOW)
        # Without fuzzing, same inputs produce same outputs
        assert r1.fsrs_due == r2.fsrs_due
