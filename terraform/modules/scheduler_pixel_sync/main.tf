terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

# Cloud Scheduler -> Cloud Run job that periodically kicks the sync-pixels
# endpoint for every advertiser. In production this would be a separate
# orchestrator endpoint that fans out; the POC uses a single advertiser.

resource "google_cloud_scheduler_job" "sync_pixels" {
  name        = var.job_name
  project     = var.project_id
  region      = var.region
  description = "Hourly Meta pixel sync"
  schedule    = var.cron
  time_zone   = "UTC"

  retry_config {
    retry_count          = 3
    min_backoff_duration = "30s"
    max_backoff_duration = "300s"
  }

  http_target {
    http_method = "POST"
    uri         = "${var.service_uri}/integrations/meta/sync-pixels"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode(jsonencode({ advertiser_id = var.advertiser_id }))

    oidc_token {
      service_account_email = var.invoker_service_account
      audience              = var.service_uri
    }
  }
}
