include "root" {
  path = find_in_parent_folders()
}

locals {
  env = read_terragrunt_config(find_in_parent_folders("env.hcl")).locals
}

dependency "secrets" {
  config_path = "../secrets"
  mock_outputs = {
    secret_ids = {
      "hub-database-url"             = "hub-database-url"
      "hub-token-encryption-key"     = "hub-token-encryption-key"
      "hub-meta-oauth-client-secret" = "hub-meta-oauth-client-secret"
    }
  }
}

terraform {
  source = "../../../modules/cloud_run_service"
}

inputs = {
  project_id            = local.env.project_id
  region                = local.env.region
  service_name          = "hub-meta-conversion-${local.env.env}"
  service_account_email = local.env.service_sa
  image                 = "us-central1-docker.pkg.dev/${local.env.project_id}/hub/meta-conversion:latest"
  app_env               = local.env.env
  meta_use_mock         = false
  min_instances         = 0
  max_instances         = 3
  vpc_connector         = "projects/${local.env.project_id}/locations/${local.env.region}/connectors/hub-vpc-connector"

  database_url_secret_id             = dependency.secrets.outputs.secret_ids["hub-database-url"]
  token_encryption_key_secret_id     = dependency.secrets.outputs.secret_ids["hub-token-encryption-key"]
  meta_oauth_client_secret_secret_id = dependency.secrets.outputs.secret_ids["hub-meta-oauth-client-secret"]

  invoker_members = [
    "serviceAccount:${local.env.scheduler_sa}",
  ]
}
