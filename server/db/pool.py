# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

"""Database connection pool and FastAPI lifespan integration."""

import os
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

_pool: AsyncConnectionPool | None = None

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://languagelearn:languagelearn@db:5432/languagelearn",
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Open the connection pool on startup, close on shutdown."""
    global _pool  # noqa: PLW0603
    _pool = AsyncConnectionPool(conninfo=DATABASE_URL, min_size=2, max_size=10)
    await _pool.open()
    try:
        yield
    finally:
        await _pool.close()
        _pool = None


async def get_conn() -> AsyncGenerator[AsyncConnection, None]:
    """FastAPI dependency that yields a connection from the pool."""
    if _pool is None:
        msg = "Connection pool is not initialized"
        raise RuntimeError(msg)
    async with _pool.connection() as conn:
        yield conn
