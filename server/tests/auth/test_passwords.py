# SPDX-License-Identifier: Apache-2.0
from auth.passwords import hash_password, verify_password


def test_hash_password_returns_bcrypt_hash() -> None:
    hashed = hash_password("testpassword")
    assert hashed.startswith("$2b$")


def test_verify_correct_password() -> None:
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_wrong_password() -> None:
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_hash_is_not_deterministic() -> None:
    h1 = hash_password("samepassword")
    h2 = hash_password("samepassword")
    assert h1 != h2  # different salts
