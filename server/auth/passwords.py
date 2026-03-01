# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import bcrypt

from auth.config import get_config


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt. Returns the hash as a string."""
    config = get_config()
    hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=config.bcrypt_rounds))
    return hashed.decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())
