terraform {
  required_version = ">= 1.8"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # State encryption — key supplied via TF_STATE_ENCRYPTION_KEY env var,
  # set by setup.ps1 and stored as a GitHub Actions secret.
  encryption {
    key_provider "pbkdf2" "default" {
      passphrase = var.state_encryption_key
    }
    method "aes_gcm" "default" {
      keys = key_provider.pbkdf2.default
    }
    state {
      method = method.aes_gcm.default
    }
  }
}

provider "aws" {
  region = var.aws_region
}
