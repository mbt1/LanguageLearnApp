# SPDX-License-Identifier: Apache-2.0
"""Integration tests for the graded exercise submission endpoint."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

# ── Helpers (mirror pattern from test_study.py) ───────────────


async def _register(client: httpx.AsyncClient) -> dict[str, Any]:
    resp = await client.post(
        "/v1/auth/register",
        json={
            "email": f"exercises-{datetime.now(UTC).timestamp()}@example.com",
            "password": "strongpassword",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _mini_course(slug: str | None = None) -> dict[str, Any]:
    """A 2-concept course with forward_mc and forward_typing exercises."""
    return {
        "slug": slug or f"exercises-test-{datetime.now(UTC).timestamp()}",
        "title": "Exercise Test Course",
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
                "exercises": [
                    {
                        "ref": "adios-mc-1",
                        "exercise_type": "forward_mc",
                        "data": {
                            "source": "goodbye",
                            "targets": ["adiós"],
                            "distractors": {"semantic": ["hola", "gracias"], "random": []},
                        },
                    },
                ],
            },
        ],
    }


async def _start_session(
    client: httpx.AsyncClient,
    course_id: str,
    token: str,
) -> list[dict[str, Any]]:
    resp = await client.post(
        "/v1/study/session",
        json={"course_id": course_id},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    return resp.json()["items"]  # type: ignore[no-any-return]


# ── POST /v1/exercises/submit ─────────────────────────────────


async def test_submit_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": "00000000-0000-0000-0000-000000000001",
            "exercise_type": "forward_mc",
            "user_answer": "hola",
        },
    )
    assert resp.status_code == 401


async def test_submit_correct_forward_mc(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = next(i for i in items if i["exercise_type"] == "forward_mc")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "forward_mc",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is True
    assert "correct_answer" in data
    assert "normalized_user_answer" in data
    assert "new_forward_difficulty" in data
    assert "forward_consecutive_correct" in data
    assert "new_reverse_difficulty" in data
    assert "reverse_consecutive_correct" in data
    assert "is_mastered" in data
    assert "fsrs_due" in data


async def test_submit_wrong_forward_mc_returns_correct_answer(
    client: httpx.AsyncClient,
) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = next(i for i in items if i["exercise_type"] == "forward_mc")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "forward_mc",
            "user_answer": "adiós",  # wrong
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["correct_answer"] == "hola"


async def test_submit_correct_forward_typing(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    # Start session to initialize progress, then submit a typing answer
    items = await _start_session(client, course_id, user["access_token"])
    concept_id = items[0]["concept_id"]

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": "forward_typing",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["correct"] is True


async def test_submit_case_insensitive_accepted(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    concept_id = items[0]["concept_id"]

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": "forward_typing",
            "user_answer": "Hola",  # different case
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["correct"] is True


async def test_submit_wrong_answer_resets_streak(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = next(i for i in items if i["exercise_type"] == "forward_mc")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "forward_mc",
            "user_answer": "adiós",  # wrong
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["forward_consecutive_correct"] == 0


async def test_submit_correct_advances_streak(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = next(i for i in items if i["exercise_type"] == "forward_mc")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "forward_mc",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["forward_consecutive_correct"] == 1


async def test_submit_exercise_type_without_explicit_exercise_returns_404(
    client: httpx.AsyncClient,
) -> None:
    """Submitting an exercise type without an explicit exercise returns 404."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    concept_id = items[0]["concept_id"]
    # Request cloze which doesn't have explicit exercise — no fallback, returns 404
    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": "cloze",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 404


async def test_submit_concept_without_progress(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": "00000000-0000-0000-0000-000000000001",
            "exercise_type": "forward_mc",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 404


async def _advance_forward_track(
    client: httpx.AsyncClient,
    concept_id: str,
    token: str,
) -> None:
    """Submit 6 correct forward reviews to advance from forward_mc → cloze → forward_typing."""
    headers = _auth_headers(token)
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


async def test_submit_reverse_typing(
    client: httpx.AsyncClient,
) -> None:
    """reverse_typing uses exercise data targets as correct_answer."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    # Find hola concept (correct_answer="hola")
    hola_item = next(i for i in items if i["correct_answer"] == "hola")
    concept_id = hola_item["concept_id"]

    # Advance forward track
    await _advance_forward_track(client, concept_id, user["access_token"])

    # Submit reverse_typing answer: correct answer should be "hello" (source language)
    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": "reverse_typing",
            "user_answer": "hello",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is True
    assert data["correct_answer"] == "hello"


async def test_submit_reverse_typing_wrong_answer(
    client: httpx.AsyncClient,
) -> None:
    """Wrong answer for reverse_typing is rejected."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    hola_item = next(i for i in items if i["correct_answer"] == "hola")
    concept_id = hola_item["concept_id"]

    await _advance_forward_track(client, concept_id, user["access_token"])

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": "reverse_typing",
            "user_answer": "hola",  # wrong — this is the Spanish word, not English
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["correct_answer"] == "hello"
