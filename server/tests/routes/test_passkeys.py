# SPDX-License-Identifier: Apache-2.0
"""Integration tests for passkey endpoints."""
from __future__ import annotations

from datetime import UTC, datetime

import httpx


async def _register_user(client: httpx.AsyncClient) -> dict[str, str]:
    """Register a user and return {email, access_token}."""
    email = f"pk-{datetime.now(UTC).timestamp()}@example.com"
    resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    data = resp.json()
    return {"email": email, "access_token": data["access_token"]}


async def test_passkey_register_options_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await client.post("/v1/auth/passkeys/register/options")
    assert resp.status_code in (401, 403)


async def test_passkey_register_options_returns_options(client: httpx.AsyncClient) -> None:
    user = await _register_user(client)
    resp = await client.post(
        "/v1/auth/passkeys/register/options",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "options" in data


async def test_passkey_authenticate_options_no_passkeys(client: httpx.AsyncClient) -> None:
    user = await _register_user(client)
    resp = await client.post(
        "/v1/auth/passkeys/authenticate/options",
        json={"email": user["email"]},
    )
    # User has no passkeys registered
    assert resp.status_code == 400


async def test_passkey_authenticate_options_unknown_email(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/passkeys/authenticate/options",
        json={"email": "nobody@example.com"},
    )
    assert resp.status_code == 400


async def test_list_passkeys_empty(client: httpx.AsyncClient) -> None:
    user = await _register_user(client)
    resp = await client.get(
        "/v1/auth/passkeys/",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_passkeys_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await client.get("/v1/auth/passkeys/")
    assert resp.status_code in (401, 403)


async def test_delete_passkey_not_found(client: httpx.AsyncClient) -> None:
    user = await _register_user(client)
    from uuid import uuid4

    resp = await client.delete(
        f"/v1/auth/passkeys/{uuid4()}",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert resp.status_code == 404
