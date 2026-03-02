# SPDX-License-Identifier: Apache-2.0
"""Integration tests for the study / SRS endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

# ── Helpers ───────────────────────────────────────────────────


async def _register(client: httpx.AsyncClient) -> dict[str, Any]:
    """Register a unique test user and return the response data (includes access_token)."""
    resp = await client.post(
        "/v1/auth/register",
        json={
            "email": f"study-{datetime.now(UTC).timestamp()}@example.com",
            "password": "strongpassword",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _mini_course(slug: str | None = None) -> dict[str, Any]:
    """A 2-concept course (hola → adios with prerequisite) for testing."""
    return {
        "slug": slug or f"study-test-{datetime.now(UTC).timestamp()}",
        "title": "Study Test Course",
        "source_language": "en",
        "target_language": "es",
        "concepts": [
            {
                "ref": "hola",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 1,
                "prompt": "hello",
                "target": "hola",
                "exercises": [
                    {
                        "exercise_type": "multiple_choice",
                        "prompt": "Choose 'hello'",
                        "correct_answer": "hola",
                        "distractors": ["adiós", "gracias"],
                    },
                    {
                        "exercise_type": "typing",
                        "prompt": "Type 'hello'",
                        "correct_answer": "hola",
                    },
                ],
            },
            {
                "ref": "adios",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 2,
                "prompt": "goodbye",
                "target": "adiós",
                "prerequisites": ["hola"],
                "exercises": [
                    {
                        "exercise_type": "multiple_choice",
                        "prompt": "Choose 'goodbye'",
                        "correct_answer": "adiós",
                        "distractors": ["hola", "gracias"],
                    }
                ],
            },
        ],
    }


async def _import_course(client: httpx.AsyncClient, slug: str | None = None) -> dict[str, Any]:
    resp = await client.post("/v1/courses/import", json=_mini_course(slug))
    assert resp.status_code == 201
    return resp.json()


# ── POST /v1/study/session ───────────────────────────────────


async def test_session_requires_auth(client: httpx.AsyncClient) -> None:
    course = await _import_course(client)
    resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
    )
    assert resp.status_code == 401


async def test_session_returns_new_concepts(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course = await _import_course(client)
    resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total_due_reviews" in data
    assert "new_concepts_added" in data
    assert isinstance(data["items"], list)
    assert data["new_concepts_added"] > 0


async def test_session_course_not_found(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    resp = await client.post(
        "/v1/study/session",
        json={"course_id": "00000000-0000-0000-0000-000000000001"},
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 404


async def test_session_items_have_required_fields(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course = await _import_course(client)
    resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0
    item = items[0]
    assert "concept_id" in item
    assert "exercise_type" in item
    assert "is_review" in item
    assert "prompt" in item
    assert "target" in item


# ── POST /v1/study/review ────────────────────────────────────


async def test_review_requires_auth(client: httpx.AsyncClient) -> None:
    course = await _import_course(client)
    user = await _register(client)
    session_resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=_auth_headers(user["access_token"]),
    )
    concept_id = session_resp.json()["items"][0]["concept_id"]
    resp = await client.post(
        "/v1/study/review",
        json={
            "concept_id": concept_id,
            "rating": "good",
            "exercise_type": "multiple_choice",
            "correct": True,
        },
    )
    assert resp.status_code == 401


async def test_review_success(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course = await _import_course(client)
    session_resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=_auth_headers(user["access_token"]),
    )
    concept_id = session_resp.json()["items"][0]["concept_id"]
    resp = await client.post(
        "/v1/study/review",
        json={
            "concept_id": concept_id,
            "rating": "good",
            "exercise_type": "multiple_choice",
            "correct": True,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "new_exercise_difficulty" in data
    assert "consecutive_correct" in data
    assert "is_mastered" in data
    assert "fsrs_due" in data
    assert "difficulty_advanced" in data
    assert "mastery_changed" in data


async def test_review_wrong_answer_resets_streak(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course = await _import_course(client)
    session_resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=_auth_headers(user["access_token"]),
    )
    concept_id = session_resp.json()["items"][0]["concept_id"]
    resp = await client.post(
        "/v1/study/review",
        json={
            "concept_id": concept_id,
            "rating": "again",
            "exercise_type": "multiple_choice",
            "correct": False,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["consecutive_correct"] == 0


async def test_review_concept_not_in_progress(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    resp = await client.post(
        "/v1/study/review",
        json={
            "concept_id": "00000000-0000-0000-0000-000000000001",
            "rating": "good",
            "exercise_type": "multiple_choice",
            "correct": True,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 404


# ── GET /v1/progress/{course_id} ─────────────────────────────


async def test_progress_requires_auth(client: httpx.AsyncClient) -> None:
    course = await _import_course(client)
    resp = await client.get(f"/v1/progress/{course['course_id']}")
    assert resp.status_code == 401


async def test_progress_returns_cefr_levels(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course = await _import_course(client)
    resp = await client.get(
        f"/v1/progress/{course['course_id']}",
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "course_id" in data
    assert "levels" in data
    assert isinstance(data["levels"], list)


async def test_progress_course_not_found(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    resp = await client.get(
        "/v1/progress/00000000-0000-0000-0000-000000000001",
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 404
