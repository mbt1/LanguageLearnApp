# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from fastapi import HTTPException, Request, status

from auth.config import get_config

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


async def validate_csrf(request: Request) -> None:
    """Validate Origin header for state-changing requests.

    SameSite=Lax on the refresh cookie is the primary CSRF defense.
    This origin check is defense-in-depth for cookie-bearing endpoints.
    """
    if request.method in _SAFE_METHODS:
        return
    origin = request.headers.get("origin")
    if origin is None:
        # No origin header — same-origin or non-browser client.
        # SameSite=Lax already prevents cross-site POST from sending cookies.
        return
    config = get_config()
    if origin not in config.allowed_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )
