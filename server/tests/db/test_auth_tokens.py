# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime, timedelta
from typing import Any

from psycopg import AsyncConnection

from db.queries.auth_tokens import (
    create_email_verification_token,
    create_refresh_token,
    delete_email_verification_token,
    get_email_verification_token,
    get_refresh_token,
    mark_user_email_verified,
    revoke_all_user_refresh_tokens,
    revoke_refresh_token,
)
from db.queries.users import create_user


async def _make_user(conn: AsyncConnection) -> dict[str, Any]:
    return await create_user(conn, email=f"authtest-{datetime.now(UTC).timestamp()}@x.com")


async def test_create_and_get_refresh_token(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    token_hash = "abc123hash"
    expires = datetime.now(UTC) + timedelta(days=7)
    created = await create_refresh_token(
        db_conn, user_id=user["id"], token_hash=token_hash, expires_at=expires
    )
    assert created["token_hash"] == token_hash
    assert created["revoked"] is False

    fetched = await get_refresh_token(db_conn, token_hash=token_hash)
    assert fetched is not None
    assert fetched["user_id"] == user["id"]


async def test_revoke_refresh_token(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    token_hash = "revoke-me"
    expires = datetime.now(UTC) + timedelta(days=7)
    await create_refresh_token(
        db_conn, user_id=user["id"], token_hash=token_hash, expires_at=expires
    )
    await revoke_refresh_token(db_conn, token_hash=token_hash)
    fetched = await get_refresh_token(db_conn, token_hash=token_hash)
    assert fetched is not None
    assert fetched["revoked"] is True


async def test_revoke_all_user_tokens(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    expires = datetime.now(UTC) + timedelta(days=7)
    await create_refresh_token(
        db_conn, user_id=user["id"], token_hash="token1", expires_at=expires
    )
    await create_refresh_token(
        db_conn, user_id=user["id"], token_hash="token2", expires_at=expires
    )
    await revoke_all_user_refresh_tokens(db_conn, user_id=user["id"])
    t1 = await get_refresh_token(db_conn, token_hash="token1")
    t2 = await get_refresh_token(db_conn, token_hash="token2")
    assert t1 is not None and t1["revoked"] is True
    assert t2 is not None and t2["revoked"] is True


async def test_get_nonexistent_refresh_token(db_conn: AsyncConnection) -> None:
    result = await get_refresh_token(db_conn, token_hash="does-not-exist")
    assert result is None


async def test_create_and_get_email_verification_token(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    expires = datetime.now(UTC) + timedelta(hours=24)
    created = await create_email_verification_token(
        db_conn, user_id=user["id"], token="verify-abc", expires_at=expires
    )
    assert created["token"] == "verify-abc"

    fetched = await get_email_verification_token(db_conn, token="verify-abc")
    assert fetched is not None
    assert fetched["user_id"] == user["id"]


async def test_delete_email_verification_token(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    expires = datetime.now(UTC) + timedelta(hours=24)
    await create_email_verification_token(
        db_conn, user_id=user["id"], token="delete-me", expires_at=expires
    )
    await delete_email_verification_token(db_conn, token="delete-me")
    result = await get_email_verification_token(db_conn, token="delete-me")
    assert result is None


async def test_mark_user_email_verified(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    assert user.get("email_verified") is False

    await mark_user_email_verified(db_conn, user_id=user["id"])

    from db.queries.users import get_user_by_id

    updated = await get_user_by_id(db_conn, user_id=user["id"])
    assert updated is not None
    assert updated["email_verified"] is True
