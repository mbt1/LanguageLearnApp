# SPDX-License-Identifier: Apache-2.0
"""Contract tests: study endpoint responses match OpenAPI spec schemas."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from tests.contracts.conftest import validate_response


async def _register(client: httpx.AsyncClient) -> dict[str, Any]:
    resp = await client.post(
        "/v1/auth/register",
        json={
            "email": f"contract-study-{datetime.now(UTC).timestamp()}@example.com",
            "password": "strongpassword",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _mini_course() -> dict[str, Any]:
    return {
        "slug": f"contract-study-{datetime.now(UTC).timestamp()}",
        "title": "Contract Study Course",
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
                    }
                ],
            }
        ],
    }


async def test_study_session_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any],
) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    course_id = course_resp.json()["course_id"]

    resp = await client.post(
        "/v1/study/session",
        json={"course_id": course_id},
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    validate_response(openapi_spec, "/v1/study/session", "post", 200, resp.json())


async def test_study_review_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any],
) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    course_id = course_resp.json()["course_id"]

    session_resp = await client.post(
        "/v1/study/session",
        json={"course_id": course_id},
        headers=_auth_headers(user["access_token"]),
    )
    concept_id = session_resp.json()["items"][0]["concept_id"]

    resp = await client.post(
        "/v1/study/review",
        json={
            "concept_id": concept_id,
            "rating": "good",
            "exercise_type": "translate",
            "difficulty": 10,
            "correct": True,
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    validate_response(openapi_spec, "/v1/study/review", "post", 200, resp.json())


async def test_course_progress_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any],
) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    course_id = course_resp.json()["course_id"]

    resp = await client.get(
        f"/v1/progress/{course_id}",
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    validate_response(openapi_spec, "/v1/progress/{course_id}", "get", 200, resp.json())
