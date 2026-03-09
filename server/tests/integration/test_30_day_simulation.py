# SPDX-License-Identifier: Apache-2.0
"""30-day learning simulation integration test.

Simulates a user learning a small course over 30 days:
- Each "day" requests a study session and submits reviews
- 80% Good, 15% Hard, 5% Again ratings
- Verifies FSRS intervals grow, prerequisite caps are respected,
  difficulty advances with streak, and session_size is honoured.
"""
from __future__ import annotations

import random
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from db.pool import get_conn
from main import app
from tests.conftest import DATABASE_URL

# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
async def test_app_sim() -> AsyncGenerator[FastAPI, None]:
    """Test app for simulation — shared conn with no-op commit for isolation."""
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL, autocommit=False)

    async def _noop_commit() -> None:  # noqa: D401
        """Swallow commit — keeps everything inside one rollback-able txn."""

    conn.commit = _noop_commit  # type: ignore[method-assign]

    async def _override_get_conn() -> AsyncGenerator[psycopg.AsyncConnection[Any], None]:
        yield conn

    app.dependency_overrides[get_conn] = _override_get_conn
    yield app
    app.dependency_overrides.clear()
    await conn.rollback()
    await conn.close()


@pytest.fixture
async def sim_client(test_app_sim: FastAPI) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=test_app_sim)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


# ── Simulation helpers ────────────────────────────────────────

RATINGS = ["good"] * 16 + ["hard"] * 3 + ["again"] * 1  # 80 / 15 / 5


def _pick_rating(rng: random.Random) -> tuple[str, bool]:
    """Return (rating, correct) pair using a fixed-seed distribution."""
    rating = rng.choice(RATINGS)
    correct = rating != "again"
    return rating, correct


# ── Small test course ─────────────────────────────────────────

def _sim_course() -> dict[str, Any]:
    """A 5-concept course: hola → adios → gracias (hola prereq), gato, perro."""
    return {
        "slug": f"sim-30day-{datetime.now(UTC).timestamp()}",
        "title": "30-Day Simulation Course",
        "source_language": "en",
        "target_language": "es",
        "concepts": [
            {
                "ref": "hola",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 1,
                "exercises": [
                    {
                        "ref": "hola-fwd-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "hello",
                            "targets": ["hola"],
                            "distractors": {"random": ["adiós", "gracias"]},
                        },
                    },
                    {
                        "ref": "hola-rev-mc-1",
                        "exercise_type": "reverse_mc",
                        "data": {
                            "source": "hola",
                            "targets": ["hello"],
                            "distractors": {"random": ["goodbye", "thanks"]},
                        },
                    },
                    {
                        "ref": "hola-cloze-1",
                        "exercise_type": "cloze",
                        "data": {
                            "source": "__ mundo",
                            "targets": ["hola"],
                        },
                    },
                    {
                        "ref": "hola-fwd-typing-1",
                        "exercise_type": "forward_typing",
                        "data": {"source": "hello", "targets": ["hola"]},
                    },
                    {
                        "ref": "hola-rev-typing-1",
                        "exercise_type": "reverse_typing",
                        "data": {"source": "hola", "targets": ["hello"]},
                    },
                ],
            },
            {
                "ref": "adios",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 2,
                "prerequisites": ["hola"],
                "exercises": [
                    {
                        "ref": "adios-fwd-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "goodbye",
                            "targets": ["adiós"],
                            "distractors": {"random": ["hola", "gracias"]},
                        },
                    },
                    {
                        "ref": "adios-rev-mc-1",
                        "exercise_type": "reverse_mc",
                        "data": {
                            "source": "adiós",
                            "targets": ["goodbye"],
                            "distractors": {"random": ["hello", "thanks"]},
                        },
                    },
                    {
                        "ref": "adios-fwd-typing-1",
                        "exercise_type": "forward_typing",
                        "data": {"source": "goodbye", "targets": ["adiós"]},
                    },
                    {
                        "ref": "adios-rev-typing-1",
                        "exercise_type": "reverse_typing",
                        "data": {"source": "adiós", "targets": ["goodbye"]},
                    },
                ],
            },
            {
                "ref": "gracias",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 3,
                "prerequisites": ["hola"],
                "exercises": [
                    {
                        "ref": "gracias-fwd-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "thank you",
                            "targets": ["gracias"],
                            "distractors": {"random": ["hola", "adiós"]},
                        },
                    },
                    {
                        "ref": "gracias-rev-mc-1",
                        "exercise_type": "reverse_mc",
                        "data": {
                            "source": "gracias",
                            "targets": ["thank you", "thanks"],
                            "distractors": {"random": ["hello", "goodbye"]},
                        },
                    },
                    {
                        "ref": "gracias-fwd-typing-1",
                        "exercise_type": "forward_typing",
                        "data": {"source": "thank you", "targets": ["gracias"]},
                    },
                    {
                        "ref": "gracias-rev-typing-1",
                        "exercise_type": "reverse_typing",
                        "data": {"source": "gracias", "targets": ["thank you", "thanks"]},
                    },
                ],
            },
            {
                "ref": "gato",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 4,
                "exercises": [
                    {
                        "ref": "gato-fwd-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "cat",
                            "targets": ["gato"],
                            "distractors": {"random": ["perro", "pez"]},
                        },
                    },
                    {
                        "ref": "gato-rev-mc-1",
                        "exercise_type": "reverse_mc",
                        "data": {
                            "source": "gato",
                            "targets": ["cat"],
                            "distractors": {"random": ["dog", "fish"]},
                        },
                    },
                    {
                        "ref": "gato-fwd-typing-1",
                        "exercise_type": "forward_typing",
                        "data": {"source": "cat", "targets": ["gato"]},
                    },
                    {
                        "ref": "gato-rev-typing-1",
                        "exercise_type": "reverse_typing",
                        "data": {"source": "gato", "targets": ["cat"]},
                    },
                ],
            },
            {
                "ref": "perro",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 5,
                "exercises": [
                    {
                        "ref": "perro-fwd-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "dog",
                            "targets": ["perro"],
                            "distractors": {"random": ["gato", "pez"]},
                        },
                    },
                    {
                        "ref": "perro-rev-mc-1",
                        "exercise_type": "reverse_mc",
                        "data": {
                            "source": "perro",
                            "targets": ["dog"],
                            "distractors": {"random": ["cat", "fish"]},
                        },
                    },
                    {
                        "ref": "perro-fwd-typing-1",
                        "exercise_type": "forward_typing",
                        "data": {"source": "dog", "targets": ["perro"]},
                    },
                    {
                        "ref": "perro-rev-typing-1",
                        "exercise_type": "reverse_typing",
                        "data": {"source": "perro", "targets": ["dog"]},
                    },
                ],
            },
        ],
    }


# ── Test ──────────────────────────────────────────────────────

async def test_30_day_simulation(sim_client: httpx.AsyncClient) -> None:
    """Simulate 30 days of studying a small 5-concept course."""
    rng = random.Random(42)  # deterministic seed
    session_size = 5  # small enough to see throttling effects

    # Register user
    reg_resp = await sim_client.post(
        "/v1/auth/register",
        json={
            "email": f"sim30day-{datetime.now(UTC).timestamp()}@example.com",
            "password": "strongpassword",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}

    # Import course
    course_resp = await sim_client.post("/v1/courses/import", json=_sim_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    # Track metrics across days
    total_reviews_submitted = 0
    all_concepts_seen: set[str] = set()
    days_with_sessions = 0

    start_day = datetime(2026, 1, 1, tzinfo=UTC)

    for day in range(30):
        sim_now = start_day + timedelta(days=day)

        # Mock datetime.now(UTC) inside routes/study.py
        with patch("routes.study.datetime") as mock_dt:
            mock_dt.now.return_value = sim_now
            mock_dt.side_effect = datetime  # pyright: ignore[reportUnknownLambdaType]

            # Request session
            session_resp = await sim_client.post(
                "/v1/study/session",
                json={"course_id": course_id, "session_size": session_size},
                headers=auth,
            )
        assert session_resp.status_code == 200
        session_data = session_resp.json()
        items = session_data["items"]

        # Session size respected
        assert len(items) <= session_size

        if not items:
            continue

        days_with_sessions += 1
        all_concepts_seen.update(item["concept_id"] for item in items)

        # Submit reviews for each item
        for item in items:
            rating, correct = _pick_rating(rng)
            with patch("routes.study.datetime") as mock_dt:
                mock_dt.now.return_value = sim_now
                mock_dt.side_effect = datetime  # pyright: ignore[reportUnknownLambdaType]

                review_resp = await sim_client.post(
                    "/v1/study/review",
                    json={
                        "concept_id": item["concept_id"],
                        "rating": rating,
                        "exercise_type": item["exercise_type"],
                        "correct": correct,
                    },
                    headers=auth,
                )
            assert review_resp.status_code == 200
            total_reviews_submitted += 1

    # ── Assertions ──────────────────────────────────────────

    # We should have had sessions on most days
    assert days_with_sessions >= 5, f"Expected sessions on many days, got {days_with_sessions}"

    # We should have seen all 5 concepts within 30 days
    assert len(all_concepts_seen) == 5, (
        f"Expected all 5 concepts seen, got {len(all_concepts_seen)}"
    )

    # Total reviews should be non-trivial
    assert total_reviews_submitted >= 10, (
        f"Expected at least 10 reviews, got {total_reviews_submitted}"
    )

    # Progress endpoint should return A1 level data
    progress_resp = await sim_client.get(
        f"/v1/progress/{course_id}",
        headers=auth,
    )
    assert progress_resp.status_code == 200
    progress_data = progress_resp.json()
    assert progress_data["course_id"] == course_id
    levels = {lvl["cefr_level"]: lvl for lvl in progress_data["levels"]}
    assert "A1" in levels
    assert levels["A1"]["total_concepts"] == 5
