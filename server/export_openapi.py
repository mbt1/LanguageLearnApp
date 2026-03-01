# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
"""Export the OpenAPI spec from the FastAPI app without starting a server.

Usage: uv run python export_openapi.py
"""
from __future__ import annotations

import json
from pathlib import Path

from main import app

spec = app.openapi()
output_path = Path(__file__).resolve().parent.parent / "api" / "v1" / "openapi.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(spec, indent=2) + "\n")
print(f"Exported OpenAPI spec to {output_path}")
