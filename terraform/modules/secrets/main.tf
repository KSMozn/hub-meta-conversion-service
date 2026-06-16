terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

resource "google_secret_manager_secret" "this" {
  for_each  = toset(var.secret_names)
  secret_id = each.value
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "accessor" {
  for_each = {
    for pair in flatten([
      for name in var.secret_names : [
        for member in var.accessor_members : {
          name   = name
          member = member
        }
      ]
    ]) : "${pair.name}|${pair.member}" => pair
  }

  project   = var.project_id
  secret_id = google_secret_manager_secret.this[each.value.name].id
  role      = "roles/secretmanager.secretAccessor"
  member    = each.value.member
}
