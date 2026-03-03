variable "aws_region" {
  description = "AWS region for the test environment."
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type. Set in terraform.tfvars."
  type        = string
}

variable "image_sha" {
  description = "GHCR image tag (git SHA) to deploy into the test environment."
  type        = string
}

variable "image_owner" {
  description = "GitHub owner used to construct GHCR image paths."
  type        = string
}

variable "state_encryption_key" {
  description = "Passphrase for OpenTofu state encryption. Supplied via TF_VAR_state_encryption_key."
  type        = string
  sensitive   = true
}

variable "run_id" {
  description = "GitHub Actions run ID, used to uniquely name resources."
  type        = string
}
