include "root" {
  path = find_in_parent_folders()
}

locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

dependency "cloud_run" {
  config_path = "../cloud_run"
  mock_outputs = {
    service_uri = "https://example.run.app"
  }
}

terraform {
  source = "../../../modules/scheduler_pixel_sync"
}

inputs = {
  project_id              = local.env.project_id
  region                  = local.env.region
  service_uri             = dependency.cloud_run.outputs.service_uri
  invoker_service_account = local.env.scheduler_sa
  cron                    = "0 * * * *"
  advertiser_id           = "00000000-0000-0000-0000-000000000000"
}
