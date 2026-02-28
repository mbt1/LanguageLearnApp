#!/usr/bin/env pwsh
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# Run database migrations using pgroll.
# Requires DATABASE_URL to be set (or uses the devcontainer default).

param(
    [switch]$Rollback,
    [switch]$Status
)

$ErrorActionPreference = 'Stop'

$appRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
# pgroll uses lib/pq which defaults to sslmode=require; our dev Postgres has no SSL.
$baseUrl = $env:DATABASE_URL ?? "postgresql://languagelearn:languagelearn@db:5432/languagelearn"
if ($baseUrl -match 'sslmode=') {
    $dbUrl = $baseUrl
} elseif ($baseUrl -match '\?') {
    $dbUrl = "${baseUrl}&sslmode=disable"
} else {
    $dbUrl = "${baseUrl}?sslmode=disable"
}
$migrationsDir = Join-Path $appRoot "server/migrations"

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

# Default: initialize pgroll (idempotent) and apply all outstanding migrations
Write-Host "Initializing pgroll..." -ForegroundColor Cyan
pgroll init --postgres-url $dbUrl 2>&1 | Out-Null

$jsonFiles = Get-ChildItem -Path $migrationsDir -Filter "*.json" -ErrorAction SilentlyContinue
if ($jsonFiles.Count -eq 0) {
    Write-Host "No migration files found in $migrationsDir" -ForegroundColor Yellow
    exit 0
}

Write-Host "Applying $($jsonFiles.Count) migration(s) from $migrationsDir..." -ForegroundColor Cyan
pgroll migrate $migrationsDir --complete --postgres-url $dbUrl
Write-Host "All migrations applied." -ForegroundColor Green
