variable "project_id" { type = string }
variable "region" { type = string }
variable "service_name" { type = string }
variable "image" { type = string }
variable "service_account_email" { type = string }

variable "app_env" {
  type    = string
  default = "prod"
}

variable "meta_use_mock" {
  type    = bool
  default = false
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "min_instances" {
  type    = number
  default = 0
}

variable "max_instances" {
  type    = number
  default = 5
}

variable "vpc_connector" {
  type        = string
  description = "Serverless VPC connector to reach Cloud SQL privately."
}

variable "database_url_secret_id" {
  type        = string
  description = "Secret Manager secret holding the SQLAlchemy DATABASE_URL."
}

variable "token_encryption_key_secret_id" {
  type        = string
  description = "Secret Manager secret holding the OAuth token cipher key."
}

variable "meta_oauth_client_secret_secret_id" {
  type        = string
  description = "Secret Manager secret holding the Meta OAuth client secret."
}

variable "invoker_members" {
  type        = list(string)
  default     = []
  description = "IAM members granted roles/run.invoker (e.g. allUsers, serviceAccount:scheduler@…)."
}
