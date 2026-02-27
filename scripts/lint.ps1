#!/usr/bin/env pwsh
# Run all linters and type checkers for both server and client.

$ErrorActionPreference = 'Stop'
$root = "$PSScriptRoot/.."
$failed = $false

Write-Host "=== Server: ruff ===" -ForegroundColor Cyan
Set-Location "$root/server"
uv run ruff check .
if ($LASTEXITCODE -ne 0) { $failed = $true }

Write-Host "`n=== Server: ruff format ===" -ForegroundColor Cyan
uv run ruff format --check .
if ($LASTEXITCODE -ne 0) { $failed = $true }

Write-Host "`n=== Server: pyright ===" -ForegroundColor Cyan
uv run pyright .
if ($LASTEXITCODE -ne 0) { $failed = $true }

Write-Host "`n=== Client: eslint ===" -ForegroundColor Cyan
Set-Location "$root/client"
pnpm lint
if ($LASTEXITCODE -ne 0) { $failed = $true }

Write-Host "`n=== Client: typecheck ===" -ForegroundColor Cyan
pnpm typecheck
if ($LASTEXITCODE -ne 0) { $failed = $true }

Write-Host "`n=== Client: prettier ===" -ForegroundColor Cyan
pnpm format:check
if ($LASTEXITCODE -ne 0) { $failed = $true }

if ($failed) {
    Write-Host "`nLint FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "`nAll checks passed!" -ForegroundColor Green
