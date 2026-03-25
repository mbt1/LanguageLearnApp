# SPDX-License-Identifier: Apache-2.0
"""Shared fixtures for route integration tests."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from db.pool import get_conn
from main import app
from tests.conftest import DATABASE_URL


@pytest.fixture
async def test_app() -> AsyncGenerator[FastAPI, None]:
    """Create test app with a single shared DB connection.

    All requests within a test share one connection whose ``commit()`` is
    a no-op so data never actually persists.  The outer transaction is
    rolled back once the test finishes, guaranteeing perfect isolation.
    """
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL, autocommit=False)

    async def _noop_commit() -> None:
        """Swallow commit — keeps everything inside one rollback-able txn."""

    conn.commit = _noop_commit  # type: ignore[method-assign]

    async def _override_get_conn() -> AsyncGenerator[psycopg.AsyncConnection[Any], None]:
        yield conn

    app.dependency_overrides[get_conn] = _override_get_conn
    # Store connection on the app so tests can access it via test_conn fixture
    app._test_conn = conn  # type: ignore[attr-defined]  # noqa: SLF001
    yield app
    app.dependency_overrides.clear()
    await conn.rollback()
    await conn.close()


@pytest.fixture
async def test_conn(test_app: FastAPI) -> psycopg.AsyncConnection[Any]:
    """Return the shared test connection for direct DB queries in tests."""
    return test_app._test_conn  # type: ignore[attr-defined]  # noqa: SLF001


@pytest.fixture
async def client(test_app: FastAPI) -> httpx.AsyncClient:
    """Async test client with cookie support."""
    transport = httpx.ASGITransport(app=test_app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")
