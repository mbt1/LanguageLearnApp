# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    @abstractmethod
    async def send_verification_email(self, to: str, verification_url: str) -> None:
        """Send an email verification message."""


class ConsoleEmailProvider(EmailProvider):
    async def send_verification_email(self, to: str, verification_url: str) -> None:
        logger.info("VERIFICATION EMAIL to=%s url=%s", to, verification_url)


_provider: EmailProvider = ConsoleEmailProvider()


def get_email_provider() -> EmailProvider:
    return _provider


def set_email_provider(provider: EmailProvider) -> None:
    global _provider  # noqa: PLW0603
    _provider = provider
