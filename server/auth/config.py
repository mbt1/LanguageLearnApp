# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    return int(raw) if raw is not None else default


@dataclass(frozen=True)
class AuthConfig:
    jwt_secret: str = field(default_factory=lambda: _env("JWT_SECRET", "dev-secret-change-me"))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = field(
        default_factory=lambda: _env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 15)
    )
    refresh_token_expire_days: int = field(
        default_factory=lambda: _env_int("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    )
    email_verification_expire_hours: int = field(
        default_factory=lambda: _env_int("EMAIL_VERIFICATION_EXPIRE_HOURS", 24)
    )
    bcrypt_rounds: int = field(default_factory=lambda: _env_int("BCRYPT_ROUNDS", 12))
    rp_id: str = field(default_factory=lambda: _env("WEBAUTHN_RP_ID", "localhost"))
    rp_name: str = field(default_factory=lambda: _env("WEBAUTHN_RP_NAME", "LanguageLearn"))
    rp_origin: str = field(
        default_factory=lambda: _env("WEBAUTHN_RP_ORIGIN", "http://localhost:5173")
    )
    allowed_origins: list[str] = field(default_factory=lambda: [
        _env("WEBAUTHN_RP_ORIGIN", "http://localhost:5173"),
    ])


_config: AuthConfig | None = None


def get_config() -> AuthConfig:
    global _config  # noqa: PLW0603
    if _config is None:
        _config = AuthConfig()
    return _config


def reset_config() -> None:
    """Reset config singleton (for testing)."""
    global _config  # noqa: PLW0603
    _config = None
