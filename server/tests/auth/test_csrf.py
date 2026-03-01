# SPDX-License-Identifier: Apache-2.0
import pytest
from fastapi import HTTPException

from auth.csrf import validate_csrf


def _make_request(method: str, origin: str | None = None):
    """Create a minimal mock Request object."""

    class FakeRequest:
        def __init__(self, method: str, origin: str | None) -> None:
            self.method = method
            self.headers = {"origin": origin} if origin else {}

    return FakeRequest(method, origin)


async def test_csrf_allows_safe_methods() -> None:
    req = _make_request("GET", origin="https://evil.com")
    await validate_csrf(req)  # type: ignore[arg-type]


async def test_csrf_allows_same_origin() -> None:
    req = _make_request("POST", origin="http://localhost:5173")
    await validate_csrf(req)  # type: ignore[arg-type]


async def test_csrf_rejects_cross_origin() -> None:
    req = _make_request("POST", origin="https://evil.com")
    with pytest.raises(HTTPException) as exc_info:
        await validate_csrf(req)  # type: ignore[arg-type]
    assert exc_info.value.status_code == 403


async def test_csrf_allows_no_origin_header() -> None:
    req = _make_request("POST")
    await validate_csrf(req)  # type: ignore[arg-type]
