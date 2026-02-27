#!/usr/bin/env pwsh
# Run database migrations using pgroll.
# Requires DATABASE_URL to be set (or uses the devcontainer default).

param(
    [string]$MigrationFile,
    [switch]$Rollback,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'

$dbUrl = $env:DATABASE_URL ?? "postgresql://languagelearn:languagelearn@db:5432/languagelearn"

if ($Status) {
    Write-Host "Migration status:" -ForegroundColor Cyan
    pgroll status --postgres-url $dbUrl
    exit 0
}

if ($Rollback) {
    Write-Host "Rolling back last migration..." -ForegroundColor Yellow
    pgroll rollback --postgres-url $dbUrl
    exit 0
}

if (-not $MigrationFile) {
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  pwsh scripts/db-migrate.ps1 -MigrationFile server/migrations/001_init.json"
    Write-Host "  pwsh scripts/db-migrate.ps1 -Rollback"
    Write-Host "  pwsh scripts/db-migrate.ps1 -Status"
    exit 1
}

Write-Host "Applying migration: $MigrationFile" -ForegroundColor Cyan
pgroll start $MigrationFile --postgres-url $dbUrl
pgroll complete --postgres-url $dbUrl
Write-Host "Migration complete." -ForegroundColor Green
