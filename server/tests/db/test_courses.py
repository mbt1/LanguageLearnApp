# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors

from uuid import uuid4

from psycopg import AsyncConnection

from db.queries.courses import create_course, get_course, list_courses


async def test_create_course(db_conn: AsyncConnection) -> None:
    course = await create_course(
        db_conn,
        slug="en-es",
        title="English to Spanish",
        source_language="en",
        target_language="es",
    )
    assert course["slug"] == "en-es"
    assert course["title"] == "English to Spanish"
    assert course["source_language"] == "en"
    assert course["target_language"] == "es"
    assert course["id"] is not None


async def test_get_course(db_conn: AsyncConnection) -> None:
    course = await create_course(
        db_conn,
        slug="en-fr",
        title="English to French",
        source_language="en",
        target_language="fr",
    )
    found = await get_course(db_conn, course_id=course["id"])
    assert found is not None
    assert found["slug"] == "en-fr"


async def test_get_course_not_found(db_conn: AsyncConnection) -> None:
    found = await get_course(db_conn, course_id=uuid4())
    assert found is None


async def test_list_courses(db_conn: AsyncConnection) -> None:
    await create_course(
        db_conn, slug="en-de", title="English to German",
        source_language="en", target_language="de",
    )
    await create_course(
        db_conn, slug="en-ar", title="English to Arabic",
        source_language="en", target_language="ar",
    )
    courses = await list_courses(db_conn)
    titles = [c["title"] for c in courses]
    assert "English to Arabic" in titles
    assert "English to German" in titles
    # Ordered by title
    assert titles.index("English to Arabic") < titles.index("English to German")
