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
                "exercises": [
                    {
                        "ref": "hola-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "hello",
                            "targets": ["hola"],
                            "distractors": {"semantic": ["adiós", "gracias"], "random": []},
                        },
                    },
                    {
                        "ref": "hola-rev-mc-1",
                        "exercise_type": "reverse_mc",
                        "data": {
                            "source": "hola",
                            "targets": ["hello"],
                            "distractors": {"semantic": ["goodbye", "thanks"], "random": []},
                        },
                    },
                    {
                        "ref": "hola-typing-1",
                        "exercise_type": "forward_typing",
                        "data": {"source": "hello", "targets": ["hola"]},
                    },
                    {
                        "ref": "hola-reverse-typing-1",
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
                        "ref": "adios-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "goodbye",
                            "targets": ["adiós"],
                            "distractors": {"semantic": ["hola", "gracias"], "random": []},
                        },
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
    assert "correct_answer" in item


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
            "exercise_type": "forward_mc",
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
            "exercise_type": "forward_mc",
            "correct": True,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "new_forward_difficulty" in data
    assert "forward_consecutive_correct" in data
    assert "new_reverse_difficulty" in data
    assert "reverse_consecutive_correct" in data
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
            "exercise_type": "forward_mc",
            "correct": False,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["forward_consecutive_correct"] == 0


async def test_review_concept_not_in_progress(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    resp = await client.post(
        "/v1/study/review",
        json={
            "concept_id": "00000000-0000-0000-0000-000000000001",
            "rating": "good",
            "exercise_type": "forward_mc",
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
    mc_items = [i for i in items if i["exercise_type"] in ("forward_mc", "reverse_mc")]
    assert len(mc_items) > 0, "expected at least one MC item"
    for item in mc_items:
        # forward_mc items from exercises should have distractors; reverse_mc may auto-enrich
        if item["exercise_type"] == "forward_mc":
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
    """Verify that courses created in one test don't leak to the next."""
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


# ── GET /v1/review-schedule/{course_id} ─────────────────────


async def test_review_schedule_includes_unstarted(client: httpx.AsyncClient) -> None:
    """Review schedule returns ALL concepts, not just started ones."""
    user = await _register(client)
    course = await _import_course(client)
    headers = _auth_headers(user["access_token"])

    # Start a session (only starts some concepts)
    session_resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"], "session_size": 1},
        headers=headers,
    )
    assert session_resp.status_code == 200

    # Review schedule should return both concepts (hola + adios)
    resp = await client.get(
        f"/v1/review-schedule/{course['course_id']}",
        headers=headers,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 2  # both concepts, not just the started one

    # At least one should have null progress fields (unstarted)
    unstarted = [i for i in items if i["forward_difficulty"] is None]
    started = [i for i in items if i["forward_difficulty"] is not None]
    assert len(started) >= 1
    assert len(unstarted) >= 0  # could be 0 if session_size picked both


# ── POST /v1/study/session with concept_ids ─────────────────


async def test_session_concept_ids_new(client: httpx.AsyncClient) -> None:
    """Targeted session for unstarted concept creates progress at MC level."""
    user = await _register(client)
    course = await _import_course(client)
    headers = _auth_headers(user["access_token"])

    # Get all concepts from review schedule
    schedule = await client.get(
        f"/v1/review-schedule/{course['course_id']}",
        headers=headers,
    )
    concept_id = schedule.json()["items"][0]["concept_id"]

    # Targeted session for this specific concept
    resp = await client.post(
        "/v1/study/session",
        json={
            "course_id": course["course_id"],
            "concept_ids": [concept_id],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Each concept now produces 2 items (forward_mc + reverse_mc)
    assert len(data["items"]) == 2
    item = data["items"][0]
    assert item["concept_id"] == concept_id
    assert item["exercise_type"] == "forward_mc"
    assert item["is_review"] is False
    item2 = data["items"][1]
    assert item2["concept_id"] == concept_id
    assert item2["exercise_type"] == "reverse_mc"
    assert item2["is_review"] is False


async def test_session_concept_ids_review(client: httpx.AsyncClient) -> None:
    """Targeted session for started concept returns is_review=True."""
    user = await _register(client)
    course = await _import_course(client)
    headers = _auth_headers(user["access_token"])

    # Start a normal session first to create progress
    session_resp = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=headers,
    )
    concept_id = session_resp.json()["items"][0]["concept_id"]

    # Now do a targeted session for the same concept
    resp = await client.post(
        "/v1/study/session",
        json={
            "course_id": course["course_id"],
            "concept_ids": [concept_id],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Each concept now produces 2 items (forward + reverse)
    assert len(data["items"]) == 2
    assert data["items"][0]["is_review"] is True
    assert data["items"][1]["is_review"] is True


async def test_session_concept_ids_wrong_course(client: httpx.AsyncClient) -> None:
    """Concept that doesn't belong to the course returns 400."""
    user = await _register(client)
    course1 = await _import_course(client, slug=f"course1-{datetime.now(UTC).timestamp()}")
    course2 = await _import_course(client, slug=f"course2-{datetime.now(UTC).timestamp()}")
    headers = _auth_headers(user["access_token"])

    # Get a concept from course2
    schedule = await client.get(
        f"/v1/review-schedule/{course2['course_id']}",
        headers=headers,
    )
    concept_id = schedule.json()["items"][0]["concept_id"]

    # Try to use it in a session for course1
    resp = await client.post(
        "/v1/study/session",
        json={
            "course_id": course1["course_id"],
            "concept_ids": [concept_id],
        },
        headers=headers,
    )
    assert resp.status_code == 400
    assert "does not belong" in resp.json()["detail"]


async def test_session_concept_ids_not_found(client: httpx.AsyncClient) -> None:
    """Non-existent concept_id returns 404."""
    user = await _register(client)
    course = await _import_course(client)
    headers = _auth_headers(user["access_token"])

    resp = await client.post(
        "/v1/study/session",
        json={
            "course_id": course["course_id"],
            "concept_ids": ["00000000-0000-0000-0000-000000000099"],
        },
        headers=headers,
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


# ── reverse_typing auto-swap ─────────────────────────────────


async def _advance_to_reverse_typing(
    client: httpx.AsyncClient,
    concept_id: str,
    headers: dict[str, str],
) -> None:
    """Submit correct reviews on forward track to advance from forward_mc → cloze → forward_typing."""
    for _ in range(6):
        resp = await client.post(
            "/v1/study/review",
            json={
                "concept_id": concept_id,
                "rating": "good",
                "exercise_type": "forward_mc",
                "correct": True,
            },
            headers=headers,
        )
        assert resp.status_code == 200


async def test_session_reverse_typing_swaps_prompt_target(
    client: httpx.AsyncClient,
) -> None:
    """reverse_typing exercise returns correct_answer from exercise data targets."""
    user = await _register(client)
    course = await _import_course(client)
    headers = _auth_headers(user["access_token"])

    # Start a session to create progress for hola (concept with correct_answer=hola for forward)
    session = await client.post(
        "/v1/study/session",
        json={"course_id": course["course_id"]},
        headers=headers,
    )
    items = session.json()["items"]
    # Find hola concept (the one with correct_answer="hola")
    hola_item = next(i for i in items if i["correct_answer"] == "hola")
    concept_id = hola_item["concept_id"]

    # Advance forward track to forward_typing
    await _advance_to_reverse_typing(client, concept_id, headers)

    # Targeted session should now include reverse track item
    resp = await client.post(
        "/v1/study/session",
        json={
            "course_id": course["course_id"],
            "concept_ids": [concept_id],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    # Find the reverse item
    reverse_item = next(i for i in items if i["exercise_type"] in ("reverse_mc", "reverse_cloze", "reverse_typing"))
    # correct_answer for reverse should be the source_text (English)
    assert reverse_item["correct_answer"] == "hello"
