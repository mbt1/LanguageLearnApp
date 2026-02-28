# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from collections.abc import AsyncGenerator, Generator
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from db.pool import get_conn
from main import app
from tests.conftest import DATABASE_URL


@pytest.fixture
def test_app() -> Generator[FastAPI, Any, None]:
    """Create test app with a real DB connection override."""

    async def _override_get_conn() -> AsyncGenerator[psycopg.AsyncConnection[Any], None]:
        conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            await conn.close()

    app.dependency_overrides[get_conn] = _override_get_conn
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app: FastAPI) -> httpx.AsyncClient:
    """Async test client (no lifespan needed — we override the DB dep)."""
    transport = httpx.ASGITransport(app=test_app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_health(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
