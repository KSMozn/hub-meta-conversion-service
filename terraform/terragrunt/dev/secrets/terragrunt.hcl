include "root" {
  path = find_in_parent_folders()
}

locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

terraform {
  source = "../../../modules/secrets"
}

inputs = {
  project_id = local.env.project_id
  region     = local.env.region
  secret_names = [
    "hub-database-url",
    "hub-token-encryption-key",
    "hub-meta-oauth-client-secret",
  ]
  accessor_members = [
    "serviceAccount:${local.env.service_sa}",
  ]
}
