# SPDX-License-Identifier: Apache-2.0
"""Integration tests for auth endpoints."""
from __future__ import annotations

from datetime import UTC, datetime

import httpx
import psycopg

from tests.conftest import DATABASE_URL

# ── Registration ─────────────────────────────────────


async def test_register_success(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/register",
        json={
            "email": f"reg-{datetime.now(UTC).timestamp()}@example.com",
            "password": "strongpassword",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "user_id" in data
    assert "access_token" in data
    assert data["message"] == "Verification email sent"
    # Refresh cookie should be set
    assert "refresh_token" in resp.cookies


async def test_register_duplicate_email(client: httpx.AsyncClient) -> None:
    email = f"dup-{datetime.now(UTC).timestamp()}@example.com"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password456"},
    )
    assert resp.status_code == 409


async def test_register_weak_password(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert resp.status_code == 422  # Pydantic validation


# ── Login ────────────────────────────────────────────


async def test_login_success(client: httpx.AsyncClient) -> None:
    email = f"login-{datetime.now(UTC).timestamp()}@example.com"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "mypassword1"},
    )
    resp = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "mypassword1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["email"] == email
    assert "refresh_token" in resp.cookies


async def test_login_wrong_password(client: httpx.AsyncClient) -> None:
    email = f"wrongpw-{datetime.now(UTC).timestamp()}@example.com"
    await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "correctpass"},
    )
    resp = await client.post(
        "/v1/auth/login",
        json={"email": email, "password": "wrongpass1"},
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


async def test_login_nonexistent_email(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "anything1"},
    )
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


# ── Refresh ──────────────────────────────────────────


async def test_refresh_success(client: httpx.AsyncClient) -> None:
    email = f"refresh-{datetime.now(UTC).timestamp()}@example.com"
    reg_resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert reg_resp.status_code == 201
    # The cookie should be available for the next request
    refresh_cookie = reg_resp.cookies.get("refresh_token")
    assert refresh_cookie is not None

    resp = await client.post(
        "/v1/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_no_cookie(client: httpx.AsyncClient) -> None:
    resp = await client.post("/v1/auth/refresh")
    assert resp.status_code == 401


async def test_refresh_rotates_token(client: httpx.AsyncClient) -> None:
    email = f"rotate-{datetime.now(UTC).timestamp()}@example.com"
    reg_resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    old_cookie = reg_resp.cookies.get("refresh_token")
    assert old_cookie is not None

    # Use the refresh token
    resp1 = await client.post(
        "/v1/auth/refresh",
        cookies={"refresh_token": old_cookie},
    )
    assert resp1.status_code == 200

    # Old refresh token should now be revoked
    resp2 = await client.post(
        "/v1/auth/refresh",
        cookies={"refresh_token": old_cookie},
    )
    assert resp2.status_code == 401


# ── Logout ───────────────────────────────────────────


async def test_logout(client: httpx.AsyncClient) -> None:
    email = f"logout-{datetime.now(UTC).timestamp()}@example.com"
    reg_resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    cookie = reg_resp.cookies.get("refresh_token")

    resp = await client.post(
        "/v1/auth/logout",
        cookies={"refresh_token": cookie} if cookie else {},
    )
    assert resp.status_code == 204


# ── Email verification ───────────────────────────────


async def test_verify_email_success(client: httpx.AsyncClient) -> None:
    # Register to create user + verification token
    email = f"verify-{datetime.now(UTC).timestamp()}@example.com"
    reg_resp = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert reg_resp.status_code == 201

    # Fetch the token directly from DB
    conn = await psycopg.AsyncConnection.connect(DATABASE_URL)
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT token FROM email_verification_tokens "
                "JOIN users ON users.id = email_verification_tokens.user_id "
                "WHERE users.email = %s",
                (email,),
            )
            row = await cur.fetchone()
            assert row is not None
            token = row[0]
    finally:
        await conn.close()

    resp = await client.get(f"/v1/auth/verify-email?token={token}")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Email verified successfully"


async def test_verify_email_invalid_token(client: httpx.AsyncClient) -> None:
    resp = await client.get("/v1/auth/verify-email?token=nonexistent-token")
    assert resp.status_code == 404


# ── Resend verification ──────────────────────────────


async def test_resend_verification_requires_auth(client: httpx.AsyncClient) -> None:
    resp = await client.post("/v1/auth/resend-verification")
    assert resp.status_code in (401, 403)
