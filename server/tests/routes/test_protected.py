# SPDX-License-Identifier: Apache-2.0
"""Integration tests for auth protection on endpoints."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import httpx

from auth.tokens import create_access_token


async def test_health_stays_public(client: httpx.AsyncClient) -> None:
    resp = await client.get("/v1/health")
    assert resp.status_code == 200


async def test_protected_endpoint_without_token(client: httpx.AsyncClient) -> None:
    # Passkey list requires auth
    resp = await client.get("/v1/auth/passkeys/")
    assert resp.status_code in (401, 403)


async def test_protected_endpoint_with_valid_token(client: httpx.AsyncClient) -> None:
    token = create_access_token(
        user_id=uuid4(),
        email="test@example.com",
        email_verified=True,
        secret="dev-secret-change-me",
    )
    resp = await client.get(
        "/v1/auth/passkeys/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


async def test_protected_endpoint_with_expired_token(client: httpx.AsyncClient) -> None:
    token = create_access_token(
        user_id=uuid4(),
        email="test@example.com",
        email_verified=True,
        secret="dev-secret-change-me",
        expires_minutes=-1,
    )
    resp = await client.get(
        "/v1/auth/passkeys/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401


async def test_resend_verification_unverified_user(client: httpx.AsyncClient) -> None:
    # Register a real user (unverified by default) with unique email
    email = f"unverified-{datetime.now(UTC).timestamp()}@example.com"
    resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    access_token = resp.json()["access_token"]

    resp = await client.post(
        "/v1/auth/resend-verification",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert resp.status_code == 204
