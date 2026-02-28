# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from typing import Annotated

from fastapi import Depends, FastAPI
from psycopg import AsyncConnection

from db.pool import get_conn, lifespan

app = FastAPI(title="LanguageLearn API", version="0.1.0", lifespan=lifespan)


@app.get("/v1/health")
async def health(
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> dict[str, str]:
    await conn.execute("SELECT 1")
    return {"status": "ok"}
