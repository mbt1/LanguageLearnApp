#!/usr/bin/env pwsh
# Start the FastAPI development server with hot reload.

$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot/../server"

Write-Host "Starting FastAPI server on http://localhost:8000 ..." -ForegroundColor Green
uv run fastapi dev main.py --host 0.0.0.0 --port 8000
