# Ephemeral Test Environment Setup

This directory contains the OpenTofu configuration for the ephemeral test
environment used by the `certify.yml` pipeline. The environment is spun up
for each certification run and torn down immediately after tests complete.

## Prerequisites

- An AWS account (free tier is sufficient for occasional use; t3.xlarge is
  not free-tier but costs < $0.05 per certification run)
- AWS CLI installed and configured with admin credentials
- GitHub CLI (`gh`) installed and authenticated to your fork
- PowerShell 7+ (`pwsh`) installed

## One-time setup

Run this from the repo root on a machine with AWS admin access:

```powershell
./infra/setup.ps1 -AwsRegion us-east-1 -GitHubRepo "your-org/LanguageLearnApp"
```

The script:
1. Creates an IAM OIDC provider for GitHub Actions
2. Creates an IAM role (`languagelearn-certify`) with a trust policy scoped
   to the `certify.yml` workflow on the `main` branch of your repository
3. Attaches a least-privilege policy (EC2 + SG create/terminate only)
4. Generates a random state encryption key
5. Writes three GitHub Actions secrets to your repository:
   - `AWS_CERTIFY_ROLE_ARN` — the IAM role to assume
   - `AWS_REGION` — the region passed in
   - `TF_STATE_ENCRYPTION_KEY` — AES-GCM key for OpenTofu state files

After setup, the `certify.yml` pipeline can be triggered via
**Actions → Certify → Run workflow** with an image SHA from a recent
`Publish` run.

## Rotating the state encryption key

```powershell
./infra/rotate-secrets.ps1 -GitHubRepo "your-org/LanguageLearnApp"
```

This generates a new key and updates the `TF_STATE_ENCRYPTION_KEY` secret.
Old encrypted state artifacts (from previous runs) become unreadable, which
is fine — they have no live resources attached to them.

## Costs

Each certification run creates one `t3.xlarge` EC2 instance for the duration
of the test suite (typically 10–20 minutes). The instance is always destroyed
at the end of the run, even on failure. Approximate cost: **< $0.10 per run**.
