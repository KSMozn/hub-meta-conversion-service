variable "project_id" { type = string }
variable "region" { type = string }
variable "instance_name" { type = string }
variable "database_name" {
  type    = string
  default = "hub"
}
variable "app_user" {
  type    = string
  default = "hub"
}
variable "tier" {
  type    = string
  default = "db-custom-2-4096"
}
variable "availability_type" {
  type    = string
  default = "ZONAL"
}
variable "private_network" {
  type        = string
  description = "VPC self-link for private IP."
}
variable "deletion_protection" {
  type    = bool
  default = true
}
