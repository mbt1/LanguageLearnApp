# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""Shared test fixtures for database integration tests."""

import os
from collections.abc import AsyncGenerator

import psycopg
import pytest
from psycopg import AsyncConnection

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://languagelearn:languagelearn@db:5432/languagelearn",
)


@pytest.fixture
async def db_conn() -> AsyncGenerator[AsyncConnection, None]:
    """Provide an async DB connection with savepoint isolation.

    Each test runs inside a transaction that is rolled back after the test,
    so tests never leave data behind and can't interfere with each other.
    """
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL, autocommit=False)
    try:
        yield conn
    finally:
        await conn.rollback()
        await conn.close()
