variable "project_id" { type = string }
variable "secret_names" { type = list(string) }
variable "accessor_members" {
  type    = list(string)
  default = []
}
