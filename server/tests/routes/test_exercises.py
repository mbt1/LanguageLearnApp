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
    """A 2-concept course with multiple_choice and typing exercises."""
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
                "exercises": [
                    {
                        "exercise_type": "multiple_choice",
                        "prompt": "Choose 'goodbye'",
                        "correct_answer": "adiós",
                        "distractors": ["hola", "gracias"],
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
            "exercise_type": "multiple_choice",
            "user_answer": "hola",
        },
    )
    assert resp.status_code == 401


async def test_submit_correct_multiple_choice(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = next(i for i in items if i["exercise_type"] == "multiple_choice")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "multiple_choice",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is True
    assert "correct_answer" in data
    assert "normalized_user_answer" in data
    assert "new_exercise_difficulty" in data
    assert "consecutive_correct" in data
    assert "is_mastered" in data
    assert "fsrs_due" in data


async def test_submit_wrong_multiple_choice_returns_correct_answer(
    client: httpx.AsyncClient,
) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = next(i for i in items if i["exercise_type"] == "multiple_choice")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "multiple_choice",
            "user_answer": "adiós",  # wrong
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["correct"] is False
    assert data["correct_answer"] == "hola"


async def test_submit_correct_typing(client: httpx.AsyncClient) -> None:
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
            "exercise_type": "typing",
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
            "exercise_type": "typing",
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
    item = next(i for i in items if i["exercise_type"] == "multiple_choice")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "multiple_choice",
            "user_answer": "adiós",  # wrong
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["consecutive_correct"] == 0


async def test_submit_correct_advances_streak(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    item = next(i for i in items if i["exercise_type"] == "multiple_choice")

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": item["concept_id"],
            "exercise_type": "multiple_choice",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["consecutive_correct"] == 1


async def test_submit_nonexistent_exercise_type(client: httpx.AsyncClient) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    # adios only has multiple_choice; requesting typing → 404
    items = await _start_session(client, course_id, user["access_token"])
    # Find adios concept_id (sequence 2)
    concept_id = next(
        i["concept_id"] for i in items if i.get("prompt") == "goodbye"
    ) if any(i.get("prompt") == "goodbye" for i in items) else None

    if concept_id is None:
        # adios not yet in session (prereq not met), use hola concept
        # and request cloze which doesn't exist for hola
        concept_id = items[0]["concept_id"]
        exercise_type = "cloze"
    else:
        exercise_type = "typing"

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": exercise_type,
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
            "exercise_type": "multiple_choice",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 404


async def _advance_to_reverse_typing(
    client: httpx.AsyncClient,
    concept_id: str,
    token: str,
) -> None:
    """Submit 6 correct reviews to advance from MC → cloze → reverse_typing."""
    headers = _auth_headers(token)
    for _ in range(6):
        resp = await client.post(
            "/v1/study/review",
            json={
                "concept_id": concept_id,
                "rating": "good",
                "exercise_type": "multiple_choice",
                "correct": True,
            },
            headers=headers,
        )
        assert resp.status_code == 200


async def test_submit_reverse_typing_without_explicit_exercise(
    client: httpx.AsyncClient,
) -> None:
    """reverse_typing with no DB exercise uses concept prompt as correct_answer."""
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    assert course_resp.status_code == 201
    course_id = course_resp.json()["course_id"]

    items = await _start_session(client, course_id, user["access_token"])
    # Find hola concept (prompt=hello, target=hola)
    hola_item = next(i for i in items if i["target"] == "hola")
    concept_id = hola_item["concept_id"]

    # Advance to reverse_typing
    await _advance_to_reverse_typing(client, concept_id, user["access_token"])

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
    hola_item = next(i for i in items if i["target"] == "hola")
    concept_id = hola_item["concept_id"]

    await _advance_to_reverse_typing(client, concept_id, user["access_token"])

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
