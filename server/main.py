# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import AsyncConnection

from auth.config import get_config
from db.pool import get_conn, lifespan
from routes.auth import router as auth_router
from routes.passkeys import router as passkeys_router

app = FastAPI(title="LanguageLearn API", version="0.1.0", lifespan=lifespan)

_config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(passkeys_router)


@app.get("/v1/health")
async def health(
    conn: Annotated[AsyncConnection, Depends(get_conn)],
) -> dict[str, str]:
    await conn.execute("SELECT 1")
    return {"status": "ok"}
