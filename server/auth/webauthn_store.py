# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredChallenge:
    challenge: bytes
    user_id: str
    created_at: float


class ChallengeStore:
    """In-memory store for WebAuthn challenges with TTL expiry."""

    def __init__(self, ttl_seconds: int = 300) -> None:
        self._store: dict[str, StoredChallenge] = {}
        self._ttl = ttl_seconds

    def store(self, key: str, challenge: bytes, user_id: str) -> None:
        self._cleanup()
        self._store[key] = StoredChallenge(
            challenge=challenge, user_id=user_id, created_at=time.time()
        )

    def pop(self, key: str) -> StoredChallenge | None:
        self._cleanup()
        return self._store.pop(key, None)

    def _cleanup(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired = [k for k, v in self._store.items() if now - v.created_at > self._ttl]
        for k in expired:
            del self._store[k]


# Module-level singleton (reset in tests)
challenge_store = ChallengeStore()
