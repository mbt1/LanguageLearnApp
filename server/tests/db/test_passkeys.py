# SPDX-License-Identifier: Apache-2.0
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from psycopg import AsyncConnection

from db.queries.passkeys import (
    create_passkey,
    delete_passkey,
    get_passkey_by_credential_id,
    list_passkeys_for_user,
    update_passkey_sign_count,
)
from db.queries.users import create_user


async def _make_user(conn: AsyncConnection) -> dict[str, Any]:
    return await create_user(conn, email=f"pk-{datetime.now(UTC).timestamp()}@x.com")


async def test_create_and_get_passkey(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    cred_id = b"\x01\x02\x03\x04"
    pub_key = b"\x05\x06\x07\x08"
    pk = await create_passkey(
        db_conn,
        user_id=user["id"],
        credential_id=cred_id,
        public_key=pub_key,
        sign_count=0,
        name="My Key",
    )
    assert pk["credential_id"] == cred_id
    assert pk["public_key"] == pub_key
    assert pk["name"] == "My Key"


async def test_get_passkey_by_credential_id(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    cred_id = b"\x10\x20\x30"
    await create_passkey(
        db_conn,
        user_id=user["id"],
        credential_id=cred_id,
        public_key=b"\xaa\xbb",
        sign_count=0,
    )
    found = await get_passkey_by_credential_id(db_conn, credential_id=cred_id)
    assert found is not None
    assert found["user_id"] == user["id"]


async def test_list_passkeys_for_user(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    await create_passkey(
        db_conn, user_id=user["id"], credential_id=b"\x01", public_key=b"\x01", sign_count=0
    )
    await create_passkey(
        db_conn, user_id=user["id"], credential_id=b"\x02", public_key=b"\x02", sign_count=0
    )
    keys = await list_passkeys_for_user(db_conn, user_id=user["id"])
    assert len(keys) == 2


async def test_update_sign_count(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    cred_id = b"\xaa"
    await create_passkey(
        db_conn, user_id=user["id"], credential_id=cred_id, public_key=b"\xbb", sign_count=0
    )
    await update_passkey_sign_count(db_conn, credential_id=cred_id, sign_count=5)
    found = await get_passkey_by_credential_id(db_conn, credential_id=cred_id)
    assert found is not None
    assert found["sign_count"] == 5


async def test_delete_passkey(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    pk = await create_passkey(
        db_conn, user_id=user["id"], credential_id=b"\xcc", public_key=b"\xdd", sign_count=0
    )
    deleted = await delete_passkey(db_conn, passkey_id=pk["id"], user_id=user["id"])
    assert deleted is True
    assert await get_passkey_by_credential_id(db_conn, credential_id=b"\xcc") is None


async def test_delete_passkey_wrong_user(db_conn: AsyncConnection) -> None:
    user = await _make_user(db_conn)
    pk = await create_passkey(
        db_conn, user_id=user["id"], credential_id=b"\xee", public_key=b"\xff", sign_count=0
    )
    deleted = await delete_passkey(db_conn, passkey_id=pk["id"], user_id=uuid4())
    assert deleted is False
