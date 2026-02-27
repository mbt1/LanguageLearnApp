#!/usr/bin/env pwsh
# Start both client and server in development mode (requires tmux or two terminals).
# In a devcontainer, run each command in separate terminals.

$ErrorActionPreference = 'Stop'

Write-Host "Starting LanguageLearn development servers..." -ForegroundColor Cyan
Write-Host ""
Write-Host "  Server: http://localhost:8000  (FastAPI + auto-reload)"
Write-Host "  Client: http://localhost:5173  (Vite HMR)"
Write-Host ""
Write-Host "Run in separate terminals:"
Write-Host "  pwsh scripts/dev-server.ps1"
Write-Host "  pwsh scripts/dev-client.ps1"
