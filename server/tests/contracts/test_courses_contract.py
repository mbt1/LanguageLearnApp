# SPDX-License-Identifier: Apache-2.0
"""Contract tests: course endpoint responses match OpenAPI spec schemas."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from tests.contracts.conftest import validate_response


def _sample_course() -> dict[str, Any]:
    """Return a valid course import payload."""
    return {
        "slug": f"contract-{datetime.now(UTC).timestamp()}",
        "title": "Contract Test Course",
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
                        "distractors": ["hola"],
                    }
                ],
            },
        ],
    }


async def test_list_courses_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    resp = await client.get("/v1/courses")
    assert resp.status_code == 200
    validate_response(openapi_spec, "/v1/courses", "get", 200, resp.json())


async def test_import_course_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    resp = await client.post("/v1/courses/import", json=_sample_course())
    assert resp.status_code == 201
    validate_response(
        openapi_spec, "/v1/courses/import", "post", 201, resp.json()
    )


async def test_get_course_detail_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    # Import a course first
    import_resp = await client.post(
        "/v1/courses/import", json=_sample_course()
    )
    course_id = import_resp.json()["course_id"]

    resp = await client.get(f"/v1/courses/{course_id}")
    assert resp.status_code == 200
    validate_response(
        openapi_spec, "/v1/courses/{course_id}", "get", 200, resp.json()
    )


async def test_list_concepts_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    import_resp = await client.post(
        "/v1/courses/import", json=_sample_course()
    )
    course_id = import_resp.json()["course_id"]

    resp = await client.get(f"/v1/courses/{course_id}/concepts")
    assert resp.status_code == 200
    validate_response(
        openapi_spec,
        "/v1/courses/{course_id}/concepts",
        "get",
        200,
        resp.json(),
    )


async def test_get_concept_detail_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    import_resp = await client.post(
        "/v1/courses/import", json=_sample_course()
    )
    course_id = import_resp.json()["course_id"]

    concepts_resp = await client.get(f"/v1/courses/{course_id}/concepts")
    concept_id = concepts_resp.json()[0]["id"]

    resp = await client.get(f"/v1/concepts/{concept_id}")
    assert resp.status_code == 200
    validate_response(
        openapi_spec,
        "/v1/concepts/{concept_id}",
        "get",
        200,
        resp.json(),
    )
