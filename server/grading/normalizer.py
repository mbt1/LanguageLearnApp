# SPDX-License-Identifier: Apache-2.0
"""Text normalization for answer grading."""
from __future__ import annotations

import re
import unicodedata


def normalize(text: str, *, strip_punctuation: bool = True) -> str:
    """Normalize an answer string for comparison.

    Steps (in order):
    1. Strip leading/trailing whitespace
    2. Collapse internal whitespace to a single space
    3. Unicode NFC normalization (composed form)
    4. Casefold (locale-aware lowercase; e.g. ß → ss)
    5. Strip punctuation (configurable)
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = unicodedata.normalize("NFC", text)
    text = text.casefold()
    if strip_punctuation:
        text = re.sub(r"[^\w\s]", "", text)
    return text
