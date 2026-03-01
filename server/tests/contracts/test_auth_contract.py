# SPDX-License-Identifier: Apache-2.0
"""Contract tests: auth endpoint responses match OpenAPI spec schemas."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from tests.contracts.conftest import validate_response


async def test_register_response_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    email = f"contract-reg-{datetime.now(UTC).timestamp()}@example.com"
    resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    validate_response(openapi_spec, "/v1/auth/register", "post", 201, resp.json())


async def test_login_response_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    email = f"contract-login-{datetime.now(UTC).timestamp()}@example.com"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    resp = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 200
    validate_response(openapi_spec, "/v1/auth/login", "post", 200, resp.json())


async def test_refresh_response_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    email = f"contract-refresh-{datetime.now(UTC).timestamp()}@example.com"
    reg = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    # Forward the refresh_token cookie from registration
    resp = await client.post("/v1/auth/refresh", cookies=dict(reg.cookies))
    assert resp.status_code == 200
    validate_response(openapi_spec, "/v1/auth/refresh", "post", 200, resp.json())


async def test_logout_no_content(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    email = f"contract-logout-{datetime.now(UTC).timestamp()}@example.com"
    reg = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    token = reg.json()["access_token"]
    resp = await client.post(
        "/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
    validate_response(openapi_spec, "/v1/auth/logout", "post", 204, None)


async def test_resend_verification_no_content(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    email = f"contract-resend-{datetime.now(UTC).timestamp()}@example.com"
    reg = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    token = reg.json()["access_token"]
    resp = await client.post(
        "/v1/auth/resend-verification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
    validate_response(openapi_spec, "/v1/auth/resend-verification", "post", 204, None)
