# -----------------------------------------------------------------------------
# Provider & Backend — SAF-Logistic AWS Infrastructure
# -----------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment and configure for remote state:
  # backend "s3" {
  #   bucket         = "saf-logistic-terraform-state"
  #   key            = "infra/terraform.tfstate"
  #   region         = "eu-west-3"
  #   dynamodb_table = "saf-logistic-terraform-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      {
        Project     = var.project
        Environment = var.environment
        ManagedBy   = "terraform"
      },
      var.tags
    )
  }
}

# ── Local values ─────────────────────────────────────────────────────────────

locals {
  prefix = "${var.project}-${var.environment}"
}
