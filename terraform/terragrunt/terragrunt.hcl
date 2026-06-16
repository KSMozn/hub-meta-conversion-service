# Root Terragrunt config. Environments inherit from this via include {}.
#
# Layout:
#   terraform/terragrunt/<env>/<component>/terragrunt.hcl
# Where <env> is dev/staging/prod and <component> is one of:
#   secrets, cloud_sql, cloud_run, scheduler.

locals {
  org_id = get_env("HUB_ORG_ID", "1234567890")
}

remote_state {
  backend = "gcs"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
  config = {
    bucket   = "hub-tfstate-${local.org_id}"
    prefix   = "${path_relative_to_include()}/terraform.tfstate"
    location = "us"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<-EOF
    provider "google" {
      project = var.project_id
      region  = var.region
    }
    variable "project_id" { type = string }
    variable "region"     { type = string }
  EOF
}
