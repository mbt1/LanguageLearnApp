#!/usr/bin/env pwsh
# SPDX-License-Identifier: Apache-2.0
# Export OpenAPI spec from FastAPI app to api/v1/openapi.json.
$ErrorActionPreference = 'Stop'
$root = "$PSScriptRoot/.."
Set-Location "$root/server"
uv run python export_openapi.py
