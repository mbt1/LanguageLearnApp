#!/usr/bin/env pwsh
# Start the Vite development server with HMR.

$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/../client"

Write-Host "Starting Vite client on http://localhost:5173 ..." -ForegroundColor Green
pnpm dev
