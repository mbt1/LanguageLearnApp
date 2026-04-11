# SPDX-License-Identifier: Apache-2.0
"""Tests for the text normalizer."""

from __future__ import annotations

from grading.normalizer import normalize


class TestNormalize:
    def test_trims_leading_and_trailing_whitespace(self) -> None:
        assert normalize("  hola  ") == "hola"

    def test_collapses_internal_whitespace(self) -> None:
        assert normalize("buenos  dias") == "buenos dias"

    def test_unicode_nfc_composed_equals_decomposed(self) -> None:
        # "é" can be U+00E9 (composed) or U+0065 U+0301 (decomposed)
        composed = "\u00e9"
        decomposed = "e\u0301"
        assert normalize(composed) == normalize(decomposed)

    def test_casefold_ascii(self) -> None:
        assert normalize("Hola") == "hola"

    def test_casefold_unicode_sharp_s(self) -> None:
        # German ß casefolds to "ss"
        assert normalize("Straße") == "strasse"

    def test_strips_punctuation_by_default(self) -> None:
        assert normalize("hello.") == "hello"
        assert normalize("¡hola!") == "hola"

    def test_strip_punctuation_false_preserves_punctuation(self) -> None:
        result = normalize("hello.", strip_punctuation=False)
        assert "." in result

    def test_empty_string_returns_empty(self) -> None:
        assert normalize("") == ""

    def test_only_whitespace_returns_empty(self) -> None:
        assert normalize("   ") == ""
