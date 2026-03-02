# SPDX-License-Identifier: Apache-2.0
"""Integration tests for course and concept browsing endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

# ── Helpers ──────────────────────────────────────────────────


def _sample_course(slug: str | None = None) -> dict[str, Any]:
    """Return a minimal valid course import payload."""
    return {
        "slug": slug or f"test-{datetime.now(UTC).timestamp()}",
        "title": "Test Course",
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
                        "distractors": ["hola", "gracias"],
                    }
                ],
            },
            {
                "ref": "ser-estar",
                "concept_type": "grammar",
                "cefr_level": "A2",
                "sequence": 1,
                "prompt": "ser vs estar",
                "target": "to be",
                "explanation": "Both mean 'to be' but are used differently.",
                "prerequisites": ["hola"],
                "exercises": [
                    {
                        "exercise_type": "multiple_choice",
                        "prompt": "Choose the correct form",
                        "correct_answer": "es",
                        "distractors": ["está", "son"],
                    },
                    {
                        "exercise_type": "typing",
                        "prompt": "Type 'he is tall'",
                        "correct_answer": "él es alto",
                    },
                ],
            },
        ],
    }


async def _import_course(
    client: httpx.AsyncClient,
    slug: str | None = None,
) -> dict[str, Any]:
    """Import a sample course and return the response data."""
    resp = await client.post("/v1/courses/import", json=_sample_course(slug))
    assert resp.status_code == 201
    return resp.json()


# ── List courses ─────────────────────────────────────────────


async def test_list_courses_returns_list(client: httpx.AsyncClient) -> None:
    resp = await client.get("/v1/courses")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_list_courses_after_import(client: httpx.AsyncClient) -> None:
    await _import_course(client)
    resp = await client.get("/v1/courses")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert "slug" in data[0]
    assert "title" in data[0]


# ── Import course ────────────────────────────────────────────


async def test_import_course_success(client: httpx.AsyncClient) -> None:
    data = await _import_course(client)
    assert "course_id" in data
    assert data["concepts_created"] == 3
    assert data["exercises_created"] == 4


async def test_import_course_invalid_json(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/v1/courses/import",
        json={"slug": "x", "title": "X"},  # missing required fields
    )
    assert resp.status_code == 422


async def test_import_course_circular_deps(
    client: httpx.AsyncClient,
) -> None:
    payload = {
        "slug": f"circ-{datetime.now(UTC).timestamp()}",
        "title": "Circular",
        "source_language": "en",
        "target_language": "es",
        "concepts": [
            {
                "ref": "a",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 1,
                "prompt": "a",
                "target": "a",
                "prerequisites": ["b"],
                "exercises": [
                    {
                        "exercise_type": "multiple_choice",
                        "prompt": "x",
                        "correct_answer": "y",
                        "distractors": ["z"],
                    }
                ],
            },
            {
                "ref": "b",
                "concept_type": "vocabulary",
                "cefr_level": "A1",
                "sequence": 2,
                "prompt": "b",
                "target": "b",
                "prerequisites": ["a"],
                "exercises": [
                    {
                        "exercise_type": "multiple_choice",
                        "prompt": "x",
                        "correct_answer": "y",
                        "distractors": ["z"],
                    }
                ],
            },
        ],
    }
    resp = await client.post("/v1/courses/import", json=payload)
    assert resp.status_code == 400
    assert "Circular dependency" in resp.json()["detail"]


async def test_import_course_duplicate_slug(
    client: httpx.AsyncClient,
) -> None:
    slug = f"dup-{datetime.now(UTC).timestamp()}"
    await _import_course(client, slug=slug)
    resp = await client.post("/v1/courses/import", json=_sample_course(slug))
    assert resp.status_code == 409


# ── Get course detail ────────────────────────────────────────


async def test_get_course_detail(client: httpx.AsyncClient) -> None:
    imported = await _import_course(client)
    course_id = imported["course_id"]

    resp = await client.get(f"/v1/courses/{course_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"].startswith("test-")
    assert "concepts_by_level" in data
    assert "A1" in data["concepts_by_level"]
    assert len(data["concepts_by_level"]["A1"]) == 2


async def test_get_course_not_found(client: httpx.AsyncClient) -> None:
    resp = await client.get(
        "/v1/courses/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404


# ── List concepts by course ──────────────────────────────────


async def test_list_concepts(client: httpx.AsyncClient) -> None:
    imported = await _import_course(client)
    course_id = imported["course_id"]

    resp = await client.get(f"/v1/courses/{course_id}/concepts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3


async def test_list_concepts_filtered_by_cefr(
    client: httpx.AsyncClient,
) -> None:
    imported = await _import_course(client)
    course_id = imported["course_id"]

    resp = await client.get(
        f"/v1/courses/{course_id}/concepts?cefr_level=A1"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(c["cefr_level"] == "A1" for c in data)


# ── Get concept detail ───────────────────────────────────────


async def test_get_concept_detail(client: httpx.AsyncClient) -> None:
    imported = await _import_course(client)
    course_id = imported["course_id"]

    # Get concepts list to find one with prerequisites
    concepts_resp = await client.get(f"/v1/courses/{course_id}/concepts")
    concepts = concepts_resp.json()
    # Find "adios" which has prerequisite "hola"
    adios = next(c for c in concepts if c["prompt"] == "goodbye")

    resp = await client.get(f"/v1/concepts/{adios['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["prompt"] == "goodbye"
    assert len(data["prerequisites"]) == 1
    assert data["prerequisites"][0]["prompt"] == "hello"
    assert len(data["exercises"]) == 1


async def test_get_concept_not_found(client: httpx.AsyncClient) -> None:
    resp = await client.get(
        "/v1/concepts/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404
