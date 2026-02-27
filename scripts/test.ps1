#!/usr/bin/env pwsh
# Run all unit tests (server pytest + client vitest).

param(
    [switch]$Coverage
)

$ErrorActionPreference = 'Stop'
$root = "$PSScriptRoot/.."
$failed = $false

Write-Host "=== Server: pytest ===" -ForegroundColor Cyan
Set-Location "$root/server"
uv run pytest
if ($LASTEXITCODE -ne 0) { $failed = $true }

Write-Host "`n=== Client: vitest ===" -ForegroundColor Cyan
Set-Location "$root/client"
if ($Coverage) {
    pnpm test:coverage
} else {
    pnpm test
}
if ($LASTEXITCODE -ne 0) { $failed = $true }

if ($failed) {
    Write-Host "`nTests FAILED" -ForegroundColor Red
    exit 1
}
Write-Host "`nAll tests passed!" -ForegroundColor Green
