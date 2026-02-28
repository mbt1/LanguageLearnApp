# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from uuid import uuid4

import psycopg.errors
import pytest
from psycopg import AsyncConnection

from db.queries.users import create_user, get_user_by_email, get_user_by_id


async def test_create_user(db_conn: AsyncConnection) -> None:
    user = await create_user(db_conn, email="test@example.com", display_name="Test")
    assert user["email"] == "test@example.com"
    assert user["display_name"] == "Test"
    assert user["id"] is not None
    assert user["password_hash"] is None


async def test_create_user_with_password(db_conn: AsyncConnection) -> None:
    user = await create_user(
        db_conn, email="pw@example.com", password_hash="hashed_pw"
    )
    assert user["password_hash"] == "hashed_pw"


async def test_get_user_by_id(db_conn: AsyncConnection) -> None:
    user = await create_user(db_conn, email="byid@example.com")
    found = await get_user_by_id(db_conn, user_id=user["id"])
    assert found is not None
    assert found["email"] == "byid@example.com"


async def test_get_user_by_id_not_found(db_conn: AsyncConnection) -> None:
    found = await get_user_by_id(db_conn, user_id=uuid4())
    assert found is None


async def test_get_user_by_email(db_conn: AsyncConnection) -> None:
    await create_user(db_conn, email="byemail@example.com")
    found = await get_user_by_email(db_conn, email="byemail@example.com")
    assert found is not None
    assert found["email"] == "byemail@example.com"


async def test_get_user_by_email_not_found(db_conn: AsyncConnection) -> None:
    found = await get_user_by_email(db_conn, email="nonexistent@example.com")
    assert found is None


async def test_create_user_duplicate_email(db_conn: AsyncConnection) -> None:
    await create_user(db_conn, email="dup@example.com")
    with pytest.raises(psycopg.errors.UniqueViolation):
        await create_user(db_conn, email="dup@example.com")
