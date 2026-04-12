#!/usr/bin/env pwsh
# Wait for a specific GitHub Actions run to complete.
#
# Usage:
#   ./scripts/WaitFor-PipelineRun.ps1 -RunId 12345
#   ./scripts/WaitFor-PipelineRun.ps1 -RunId 12345 -Interval 15 -Timeout 300

param(
    [Parameter(Mandatory)]
    [string]$RunId,

    [int]$Interval = 30,
    [int]$Timeout = 600
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$startTime = Get-Date

function Get-Run {
    $json = gh run view $RunId --json 'databaseId,status,conclusion,name,workflowName,headBranch,jobs' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Failed to fetch run ${RunId}: ${json}" }
    return $json | ConvertFrom-Json
}

Write-Host "Watching run $RunId (polling every ${Interval}s, timeout ${Timeout}s)..." -ForegroundColor Cyan

while ($true) {
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    if ($elapsed -ge $Timeout) {
        Write-Host "`nTimed out after ${Timeout}s." -ForegroundColor Red
        exit 1
    }

    $run = Get-Run

    if ($run.status -eq 'completed') {
        $color = if ($run.conclusion -eq 'success') { 'Green' } else { 'Red' }
        Write-Host "`n$($run.conclusion.ToUpper()): $($run.workflowName) — $($run.name)" -ForegroundColor $color

        foreach ($job in $run.jobs) {
            $jc = if ($job.conclusion -eq 'success') { 'Green' } elseif ($job.conclusion -eq 'failure') { 'Red' } else { 'Yellow' }
            Write-Host "  $($job.conclusion.PadRight(10)) $($job.name)" -ForegroundColor $jc
        }

        if ($run.conclusion -eq 'success') { exit 0 } else { exit 1 }
    }

    $remaining = [math]::Round($Timeout - $elapsed)
    Write-Host "  [$(Get-Date -Format 'HH:mm:ss')] $($run.workflowName) — status: $($run.status) (${remaining}s remaining)" -ForegroundColor DarkGray
    Start-Sleep -Seconds $Interval
}
