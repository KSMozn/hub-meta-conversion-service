output "connection_name" {
  value = google_sql_database_instance.this.connection_name
}

output "private_ip" {
  value = google_sql_database_instance.this.private_ip_address
}

output "database_url" {
  description = "SQLAlchemy URL with the generated password — store in Secret Manager."
  value = format(
    "postgresql+psycopg://%s:%s@%s:5432/%s",
    google_sql_user.app.name,
    random_password.app_user.result,
    google_sql_database_instance.this.private_ip_address,
    google_sql_database.app.name,
  )
  sensitive = true
}
