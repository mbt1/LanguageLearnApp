# SPDX-License-Identifier: Apache-2.0
from auth.webauthn_store import ChallengeStore


def test_store_and_pop_challenge() -> None:
    store = ChallengeStore(ttl_seconds=60)
    store.store("key1", b"challenge-bytes", "user-123")
    result = store.pop("key1")
    assert result is not None
    assert result.challenge == b"challenge-bytes"
    assert result.user_id == "user-123"


def test_pop_nonexistent_returns_none() -> None:
    store = ChallengeStore(ttl_seconds=60)
    assert store.pop("no-such-key") is None


def test_expired_challenge_cleaned_up() -> None:
    store = ChallengeStore(ttl_seconds=0)  # immediate expiry
    store.store("key1", b"data", "user")
    import time

    time.sleep(0.01)
    assert store.pop("key1") is None


def test_pop_is_single_use() -> None:
    store = ChallengeStore(ttl_seconds=60)
    store.store("key1", b"data", "user")
    store.pop("key1")
    assert store.pop("key1") is None
