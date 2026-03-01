#!/usr/bin/env pwsh
# SPDX-License-Identifier: Apache-2.0
# Export OpenAPI spec and generate TypeScript types from it.
$ErrorActionPreference = 'Stop'
$root = "$PSScriptRoot/.."

# Step 1: Export fresh spec
& "$PSScriptRoot/export-openapi.ps1"

# Step 2: Generate TypeScript types
Write-Host "Generating TypeScript types from OpenAPI spec..." -ForegroundColor Cyan
Set-Location $root
npx openapi-typescript api/v1/openapi.json -o client/src/api/types.gen.d.ts
Write-Host "Types generated at client/src/api/types.gen.d.ts" -ForegroundColor Green
