# SPDX-License-Identifier: Apache-2.0
"""Tests that the committed OpenAPI spec is valid and matches the server."""
from __future__ import annotations

import json
from pathlib import Path

from openapi_spec_validator import validate

SPEC_PATH = Path(__file__).resolve().parent.parent.parent / "api" / "v1" / "openapi.json"


def test_committed_spec_is_valid_openapi() -> None:
    """The committed api/v1/openapi.json must be a valid OpenAPI 3.1 document."""
    assert SPEC_PATH.exists(), f"OpenAPI spec not found at {SPEC_PATH}"
    spec = json.loads(SPEC_PATH.read_text())
    validate(spec)


def test_committed_spec_matches_server() -> None:
    """The committed spec must match what the FastAPI app generates."""
    assert SPEC_PATH.exists(), f"OpenAPI spec not found at {SPEC_PATH}"
    committed = json.loads(SPEC_PATH.read_text())

    from main import app

    live = app.openapi()
    assert committed == live, (
        "OpenAPI spec drift detected! "
        "Run `pwsh scripts/generate-types.ps1` and commit the updated api/v1/openapi.json"
    )
