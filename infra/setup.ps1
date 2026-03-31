#!/usr/bin/env pwsh
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 LanguageLearn Contributors
#
# One-time setup: creates the AWS OIDC provider + IAM role for the certify
# pipeline and writes the required GitHub Actions secrets.
#
# Usage:
#   ./infra/setup.ps1 -AwsRegion us-east-1 -GitHubRepo "your-org/LanguageLearnApp"

param(
    [Parameter(Mandatory)]
    [string]$AwsRegion,

    [Parameter(Mandatory)]
    [string]$GitHubRepo   # e.g. "my-org/LanguageLearnApp"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$GitHubOrg  = $GitHubRepo.Split('/')[0]
$RepoName   = $GitHubRepo.Split('/')[1]
$RoleName   = 'languagelearn-certify'
$PolicyName = 'languagelearn-certify-policy'

Write-Host "`n=== LanguageLearn certify pipeline setup ===" -ForegroundColor Cyan

# ── 1. OIDC provider ──────────────────────────────────────────────────────────
Write-Host "`n[1/5] Creating GitHub Actions OIDC provider..."

$OidcUrl  = 'https://token.actions.githubusercontent.com'
$Thumbprint = '6938fd4d98bab03faadb97b34396831e3780aea1'  # GitHub's OIDC thumbprint

$ExistingProviders = aws iam list-open-id-connect-providers --query 'OpenIDConnectProviderList[].Arn' --output text
if ($ExistingProviders -match 'token\.actions\.githubusercontent\.com') {
    Write-Host "  OIDC provider already exists, skipping." -ForegroundColor Yellow
    $OidcArn = ($ExistingProviders -split '\s+' | Where-Object { $_ -match 'token\.actions' })[0]
} else {
    $OidcArn = aws iam create-open-id-connect-provider `
        --url $OidcUrl `
        --client-id-list 'sts.amazonaws.com' `
        --thumbprint-list $Thumbprint `
        --query 'OpenIDConnectProviderArn' --output text
    Write-Host "  Created: $OidcArn" -ForegroundColor Green
}

# ── 2. IAM role ───────────────────────────────────────────────────────────────
Write-Host "`n[2/5] Creating IAM role '$RoleName'..."

$AccountId = aws sts get-caller-identity --query Account --output text

$TrustPolicy = @{
    Version   = '2012-10-17'
    Statement = @(@{
        Effect    = 'Allow'
        Principal = @{ Federated = $OidcArn }
        Action    = 'sts:AssumeRoleWithWebIdentity'
        Condition = @{
            StringEquals = @{
                'token.actions.githubusercontent.com:aud' = 'sts.amazonaws.com'
                # Scoped to certify.yml on main only
                'token.actions.githubusercontent.com:sub' = "repo:${GitHubOrg}/${RepoName}:workflow_ref:${GitHubOrg}/${RepoName}/.github/workflows/certify.yml@refs/heads/main"
            }
        }
    })
} | ConvertTo-Json -Depth 10 -Compress

$ExistingRole = aws iam get-role --role-name $RoleName --query 'Role.Arn' --output text 2>$null
if ($ExistingRole) {
    Write-Host "  Role already exists: $ExistingRole" -ForegroundColor Yellow
    $RoleArn = $ExistingRole
} else {
    $RoleArn = aws iam create-role `
        --role-name $RoleName `
        --assume-role-policy-document $TrustPolicy `
        --query 'Role.Arn' --output text
    Write-Host "  Created: $RoleArn" -ForegroundColor Green
}

# ── 3. IAM policy ─────────────────────────────────────────────────────────────
Write-Host "`n[3/5] Attaching least-privilege policy..."

$Policy = @{
    Version   = '2012-10-17'
    Statement = @(
        @{
            Effect   = 'Allow'
            Action   = @(
                'ec2:RunInstances', 'ec2:TerminateInstances', 'ec2:DescribeInstances',
                'ec2:DescribeInstanceStatus', 'ec2:DescribeImages', 'ec2:DescribeVpcs',
                'ec2:DescribeSubnets', 'ec2:CreateSecurityGroup', 'ec2:DeleteSecurityGroup',
                'ec2:AuthorizeSecurityGroupIngress', 'ec2:AuthorizeSecurityGroupEgress',
                'ec2:RevokeSecurityGroupEgress', 'ec2:DescribeSecurityGroups',
                'ec2:CreateTags', 'ec2:DescribeTags'
            )
            Resource = '*'
        }
    )
} | ConvertTo-Json -Depth 10 -Compress

$PolicyArn = "arn:aws:iam::${AccountId}:policy/${PolicyName}"
$ExistingPolicy = aws iam get-policy --policy-arn $PolicyArn --query 'Policy.Arn' --output text 2>$null
if ($ExistingPolicy) {
    # Update existing policy
    $VersionId = aws iam create-policy-version `
        --policy-arn $PolicyArn `
        --policy-document $Policy `
        --set-as-default `
        --query 'PolicyVersion.VersionId' --output text
    Write-Host "  Updated policy, version $VersionId" -ForegroundColor Yellow
} else {
    $PolicyArn = aws iam create-policy `
        --policy-name $PolicyName `
        --policy-document $Policy `
        --query 'Policy.Arn' --output text
    Write-Host "  Created: $PolicyArn" -ForegroundColor Green
}

aws iam attach-role-policy --role-name $RoleName --policy-arn $PolicyArn
Write-Host "  Policy attached." -ForegroundColor Green

# ── 4. GitHub secrets ─────────────────────────────────────────────────────────
Write-Host "`n[4/4] Writing GitHub Actions secrets to $GitHubRepo..."
gh secret set AWS_CERTIFY_ROLE_ARN   --body $RoleArn      --repo $GitHubRepo
gh secret set AWS_REGION             --body $AwsRegion    --repo $GitHubRepo
Write-Host "  Secrets written." -ForegroundColor Green

Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan
Write-Host "You can now trigger the certify pipeline via:"
Write-Host "  gh workflow run certify.yml --repo $GitHubRepo -f image_sha=<SHA>"
