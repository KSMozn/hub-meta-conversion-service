include "root" {
  path = find_in_parent_folders()
}

locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

terraform {
  source = "../../../modules/cloud_sql"
}

inputs = {
  project_id          = local.env.project_id
  region              = local.env.region
  instance_name       = "hub-${local.env.env}-pg"
  tier                = "db-custom-1-3840"
  availability_type   = "ZONAL"
  deletion_protection = false
  private_network     = "projects/${local.env.project_id}/global/networks/default"
}
