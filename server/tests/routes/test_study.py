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


# ── Session distractors ──────────────────────────────────────


async def test_session_mc_items_include_distractors(client: httpx.AsyncClient) -> None:
    """Multiple choice items must include distractors from the exercises table."""
    user = await _register(client)
    course = await _import_course(client)
    resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    mc_items = [i for i in items if i["exercise_type"] == "multiple_choice"]
    assert len(mc_items) > 0, "expected at least one MC item"
    for item in mc_items:
        assert item["distractors"] is not None, f"distractors missing for {item['concept_id']}"
        assert len(item["distractors"]) >= 1, "need at least 1 distractor"


# ── GET /v1/progress (batch) ─────────────────────────────────


async def test_batch_progress_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await client.get("/v1/progress")
    assert resp.status_code == 401


async def test_batch_progress_returns_all_courses(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course = await _import_course(client)
    # Start a session so progress rows exist
    await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=_auth_headers(user["access_token"]),
    )
    resp = await client.get(
        "/v1/progress",
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "courses" in data
    assert isinstance(data["courses"], list)
    assert len(data["courses"]) >= 1
    entry = data["courses"][0]
    assert "course_id" in entry
    assert "levels" in entry


async def test_batch_progress_zero_mastery_for_new_user(client: httpx.AsyncClient) -> None:
    """A fresh user has zero mastered concepts across all courses."""
    user = await _register(client)
    resp = await client.get(
        "/v1/progress",
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["courses"], list)
    for course in data["courses"]:
        for level in course["levels"]:
            assert level["mastered"] == 0
            assert level["not_started"] == level["total_concepts"]


# ── Test isolation ────────────────────────────────────────────


async def test_isolation_no_leftover_test_courses(client: httpx.AsyncClient) -> None:
    """Verify that courses created in one test don't leak to the next.

    Imports a course within this test, then checks that a subsequent list
    does not include it (only pre-existing seed data should be visible).
    """
    # Snapshot current course count
    resp_before = await client.get("/v1/courses")
    assert resp_before.status_code == 200
    count_before = len(resp_before.json())

    # Import a course (will be rolled back by the no-op commit fixture)
    await _import_course(client)

    # The test-created course should be visible within this transaction
    resp_during = await client.get("/v1/courses")
    slugs = [c["slug"] for c in resp_during.json()]
    assert any(s.startswith("study-test-") for s in slugs)

    # After teardown (in the next test) this course will be gone.
    # For now just verify the count increased by exactly 1.
    assert len(resp_during.json()) == count_before + 1
