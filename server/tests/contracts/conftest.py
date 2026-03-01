# SPDX-License-Identifier: Apache-2.0
"""Fixtures for contract tests that validate responses against OpenAPI schemas."""
from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from typing import Any

import httpx
import jsonschema
import psycopg
import pytest
from fastapi import FastAPI

from db.pool import get_conn
from main import app
from tests.conftest import DATABASE_URL

SPEC_PATH = Path(__file__).resolve().parent.parent.parent.parent / "api" / "v1" / "openapi.json"


@pytest.fixture(scope="session")
def openapi_spec() -> dict[str, Any]:
    """Load the committed OpenAPI spec."""
    return json.loads(SPEC_PATH.read_text())


@pytest.fixture
def test_app() -> Generator[FastAPI, Any, None]:
    """Create test app with a real DB connection override."""

    async def _override_get_conn() -> AsyncGenerator[psycopg.AsyncConnection[Any], None]:
        conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            await conn.rollback()
            await conn.close()

    app.dependency_overrides[get_conn] = _override_get_conn
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app: FastAPI) -> httpx.AsyncClient:
    """Async test client with cookie support."""
    transport = httpx.ASGITransport(app=test_app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _resolve_ref(spec: dict[str, Any], ref: str) -> dict[str, Any]:
    """Resolve a $ref pointer within the spec."""
    parts = ref.lstrip("#/").split("/")
    node: Any = spec
    for part in parts:
        node = node[part]
    return node


def validate_response(
    spec: dict[str, Any],
    path: str,
    method: str,
    status_code: int,
    response_data: Any,
) -> None:
    """Validate a response body against the OpenAPI spec schema."""
    path_item = spec["paths"].get(path)
    assert path_item is not None, f"Path {path} not found in spec"

    operation = path_item.get(method)
    assert operation is not None, f"Method {method} not found for {path}"

    response_spec = operation["responses"].get(str(status_code))
    assert response_spec is not None, (
        f"Status {status_code} not in spec for {method.upper()} {path}"
    )

    # 204 No Content — no body to validate
    if "content" not in response_spec:
        return

    media = response_spec["content"]["application/json"]
    schema = media["schema"]

    # Resolve top-level $ref
    if "$ref" in schema:
        schema = _resolve_ref(spec, schema["$ref"])

    # Use jsonschema with a resolver for nested $refs
    registry = jsonschema.RefResolver.from_schema(spec)  # pyright: ignore[reportUnknownVariableType,reportUnknownMemberType]
    jsonschema.validate(response_data, schema, resolver=registry)
