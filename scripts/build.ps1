#!/usr/bin/env pwsh
# Build the client for production.

$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/../client"

Write-Host "Building client..." -ForegroundColor Cyan
pnpm build

Write-Host "Build complete: client/dist/" -ForegroundColor Green
