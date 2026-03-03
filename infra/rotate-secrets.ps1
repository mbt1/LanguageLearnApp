#!/usr/bin/env pwsh
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# Rotates the OpenTofu state encryption key.
# Old state artifacts from previous runs become unreadable — this is safe
# because all previous test environments have already been destroyed.
#
# Usage:
#   ./infra/rotate-secrets.ps1 -GitHubRepo "your-org/LanguageLearnApp"

param(
    [Parameter(Mandatory)]
    [string]$GitHubRepo
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "`n=== Rotating TF_STATE_ENCRYPTION_KEY ===" -ForegroundColor Cyan

$NewKey = [System.Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Maximum 256) }))
gh secret set TF_STATE_ENCRYPTION_KEY --body $NewKey --repo $GitHubRepo

Write-Host "Key rotated. Any in-flight certify runs using the old key will fail" -ForegroundColor Yellow
Write-Host "state decryption — re-trigger them after rotation completes." -ForegroundColor Yellow
Write-Host "`nDone." -ForegroundColor Green
