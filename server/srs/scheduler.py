# SPDX-License-Identifier: Apache-2.0
"""FSRS scheduling wrapper — pure Python, no DB imports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fsrs import Card, Rating, Scheduler, State

DESIRED_RETENTION = 0.9
MASTERY_STABILITY_THRESHOLD = 180.0

_STATE_MAP: dict[str, State] = {s.name.lower(): s for s in State}
_RATING_MAP: dict[str, Rating] = {
    "again": Rating.Again,
    "hard": Rating.Hard,
    "good": Rating.Good,
    "easy": Rating.Easy,
}


@dataclass(frozen=True, slots=True)
class ReviewResult:
    """Fields to persist back to user_concept_progress after a review."""

    fsrs_state: str
    fsrs_step: int | None
    fsrs_stability: float | None
    fsrs_difficulty: float | None
    fsrs_due: datetime
    fsrs_last_review: datetime


def create_new_card(now: datetime) -> Card:
    """Create a fresh FSRS card for a first encounter."""
    card = Card()
    card.due = now
    return card


def reconstruct_card(
    *,
    fsrs_state: str | None,
    fsrs_step: int | None,
    fsrs_stability: float | None,
    fsrs_difficulty: float | None,
    fsrs_due: datetime | None,
    fsrs_last_review: datetime | None,
) -> Card:
    """Rebuild an FSRS Card from DB column values."""
    if fsrs_state is None:
        return create_new_card(fsrs_due or datetime.now(UTC))
    card = Card()
    card.state = _STATE_MAP[fsrs_state]
    card.step = fsrs_step
    card.stability = fsrs_stability
    card.difficulty = fsrs_difficulty
    card.due = fsrs_due or datetime.now(UTC)
    card.last_review = fsrs_last_review
    return card


def parse_rating(rating_str: str) -> Rating:
    """Convert a lowercase rating string to an fsrs Rating enum."""
    rating = _RATING_MAP.get(rating_str)
    if rating is None:
        msg = f"Unknown rating: {rating_str!r}"
        raise ValueError(msg)
    return rating


def process_review(
    card: Card,
    rating: Rating,
    now: datetime,
    *,
    enable_fuzzing: bool = False,
) -> ReviewResult:
    """Run FSRS scheduling and return a ReviewResult for DB persistence."""
    scheduler = Scheduler(
        desired_retention=DESIRED_RETENTION,
        enable_fuzzing=enable_fuzzing,
    )
    new_card, _log = scheduler.review_card(card, rating, now)
    return ReviewResult(
        fsrs_state=new_card.state.name.lower(),
        fsrs_step=new_card.step,
        fsrs_stability=new_card.stability,
        fsrs_difficulty=new_card.difficulty,
        fsrs_due=new_card.due,
        fsrs_last_review=new_card.last_review or now,
    )
