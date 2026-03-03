# Test environment sizing.
# Larger than prod (t4g.small) so E2E tests finish quickly.
# No secrets here — all sensitive values come from GitHub Actions secrets.
instance_type = "t3.xlarge"
aws_region    = "us-east-1"
