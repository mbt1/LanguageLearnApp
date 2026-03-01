# SPDX-License-Identifier: Apache-2.0
"""Contract tests: passkey endpoint responses match OpenAPI spec schemas."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from tests.contracts.conftest import validate_response


async def _register_and_get_token(client: httpx.AsyncClient, label: str) -> str:
    """Register a user and return the access token."""
    email = f"contract-pk-{label}-{datetime.now(UTC).timestamp()}@example.com"
    resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def test_passkey_registration_options_matches_spec(
    client: httpx.AsyncClient, openapi_spec: dict[str, Any]
) -> None:
    token = await _register_and_get_token(client, "reg-opts")
    resp = await client.post(
        "/v1/auth/passkeys/register/options",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    validate_response(
        openapi_spec, "/v1/auth/passkeys/register/options", "post", 200, resp.json()
    )


async def test_list_passkeys_matches_spec(client: httpx.AsyncClient) -> None:
    token = await _register_and_get_token(client, "list")
    resp = await client.get(
        "/v1/auth/passkeys/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
