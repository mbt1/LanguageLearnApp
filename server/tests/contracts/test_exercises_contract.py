# SPDX-License-Identifier: Apache-2.0
"""Contract tests: exercise submission response matches OpenAPI spec schema."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from tests.contracts.conftest import validate_response


async def _register(client: httpx.AsyncClient) -> dict[str, Any]:
    resp = await client.post(
        "/v1/auth/register",
        json={
            "email": f"contract-ex-{datetime.now(UTC).timestamp()}@example.com",
            "password": "strongpassword",
        },
    )
    assert resp.status_code == 201
    return resp.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _mini_course() -> dict[str, Any]:
    return {
        "slug": f"contract-ex-{datetime.now(UTC).timestamp()}",
        "title": "Contract Exercise Course",
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
                    }
                ],
            }
        ],
    }


async def test_exercise_submit_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any],
) -> None:
    user = await _register(client)
    course_resp = await client.post("/v1/courses/import", json=_mini_course())
    course_id = course_resp.json()["course_id"]

    # Initialize progress via session
    session_resp = await client.post(
        "/v1/study/session",
        json={"course_id": course_id},
        headers=_auth_headers(user["access_token"]),
    )
    concept_id = session_resp.json()["items"][0]["concept_id"]

    resp = await client.post(
        "/v1/exercises/submit",
        json={
            "concept_id": concept_id,
            "exercise_type": "multiple_choice",
            "user_answer": "hola",
        },
        headers=_auth_headers(user["access_token"]),
    )
    assert resp.status_code == 200
    validate_response(openapi_spec, "/v1/exercises/submit", "post", 200, resp.json())
