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
    """A 2-concept course with translate and cloze exercises."""
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
                        "ref": "hola-translate-1",
                        "exercise_type": "translate",
                        "data": {
                            "prompt": ["hello"],
                            "answers": [["hola"]],
                            "distractors": {"semantic": ["adiós", "gracias"]},
                        },
                    },
                    {
                        "ref": "hola-reverse-1",
                        "exercise_type": "translate",
                        "reverse": True,
                        "data": {"prompt": ["hola"], "answers": [["hello"]]},
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
                        "ref": "adios-translate-1",
                        "exercise_type": "translate",
                        "data": {
                            "prompt": ["goodbye"],
                            "answers": [["adiós"]],
                            "distractors": {"semantic": ["hola", "gracias"]},
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
            "exercise_type": "translate",
            "difficulty": 10,
            "user_answer": "hola",
        },
    )
    assert resp.status_code == 401


async def test_submit_correct_answer(client: httpx.AsyncClient) -> None:
    """Submit the first correct answer from the session item."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = items[0]
    correct_answer = item["correct_answers"][0]

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": item["exercise_type"],
            "difficulty": item["difficulty"],
            "exercise_id": item["exercise_id"],
            "user_answer": correct_answer,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is True
    assert "correct_answer" in data
    assert "normalized_user_answer" in data
    assert "difficulty" in data
    assert "peak_difficulty" in data
    assert "is_mastered" in data
    assert "fsrs_due" in data


async def test_submit_wrong_answer(client: httpx.AsyncClient) -> None:
    """Wrong answer returns correct=False and the correct answer."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = items[0]
    correct_answer = item["correct_answers"][0]

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": item["exercise_type"],
            "difficulty": item["difficulty"],
            "exercise_id": item["exercise_id"],
            "user_answer": "zzz_definitely_wrong",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["correct_answer"] == correct_answer


async def test_submit_case_insensitive_accepted(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = items[0]
    # Submit the correct answer with different casing
    correct_answer = item["correct_answers"][0]
    cased_answer = correct_answer[0].upper() + correct_answer[1:]

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": item["exercise_type"],
            "difficulty": item["difficulty"],
            "exercise_id": item["exercise_id"],
            "user_answer": cased_answer,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["correct"] is True


async def test_submit_correct_peak_difficulty(client: httpx.AsyncClient) -> None:
    """Correct answer records peak_difficulty >= submitted difficulty."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = items[0]

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": item["exercise_type"],
            "difficulty": item["difficulty"],
            "exercise_id": item["exercise_id"],
            "user_answer": item["correct_answers"][0],
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["peak_difficulty"] >= 10


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
    # Request match which doesn't have explicit exercise — no fallback, returns 404
    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": "match",
            "difficulty": 10,
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
            "exercise_type": "translate",
            "difficulty": 10,
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 404


async def test_submit_with_exercise_id(client: httpx.AsyncClient) -> None:
    """Submitting with exercise_id uses that specific exercise for grading."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = items[0]
    assert item["exercise_id"] is not None

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": item["exercise_type"],
            "difficulty": item["difficulty"],
            "exercise_id": item["exercise_id"],
            "user_answer": item["correct_answers"][0],
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["correct"] is True
