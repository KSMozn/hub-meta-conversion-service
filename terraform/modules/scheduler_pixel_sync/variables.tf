variable "project_id" { type = string }
variable "region" { type = string }
variable "job_name" {
  type    = string
  default = "hub-meta-pixel-sync"
}
variable "cron" {
  type    = string
  default = "0 * * * *"
}
variable "service_uri" {
  type        = string
  description = "Cloud Run service base URL."
}
variable "advertiser_id" {
  type        = string
  description = "Advertiser UUID to sync. (Production would call a multi-advertiser endpoint.)"
}
variable "invoker_service_account" {
  type        = string
  description = "Service account email Scheduler signs OIDC tokens as."
}
