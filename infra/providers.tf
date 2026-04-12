terraform {
  required_version = ">= 1.8"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # State is not encrypted — this environment is ephemeral (lives ~10 min)
  # and the state contains only public EC2 metadata + hardcoded test credentials.
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      LanguageLearnApp_Ephemeral              = "true"
      "LanguageLearnApp_Ephemeral_${var.run_id}" = "true"
    }
  }
}
