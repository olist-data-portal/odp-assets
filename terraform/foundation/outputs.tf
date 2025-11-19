# VPC and Network
output "vpc_id" {
  description = "VPC Network ID"
  value       = google_compute_network.main.id
}

output "vpc_name" {
  description = "VPC Network name"
  value       = google_compute_network.main.name
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = google_compute_subnetwork.public[*].id
}

output "public_subnet_names" {
  description = "Public subnet names"
  value       = google_compute_subnetwork.public[*].name
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = google_compute_subnetwork.private[*].id
}

output "private_subnet_names" {
  description = "Private subnet names"
  value       = google_compute_subnetwork.private[*].name
}

# Firewall Rules
output "alb_firewall_rule_id" {
  description = "ALB firewall rule ID"
  value       = google_compute_firewall.alb.id
}

output "web_firewall_rule_id" {
  description = "Web firewall rule ID"
  value       = google_compute_firewall.web.id
}

output "daemon_firewall_rule_id" {
  description = "Daemon firewall rule ID"
  value       = google_compute_firewall.daemon.id
}

output "user_code_firewall_rule_id" {
  description = "User code firewall rule ID"
  value       = google_compute_firewall.user_code.id
}

# Cloud SQL
output "cloud_sql_instance_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "cloud_sql_instance_ip_address" {
  description = "Cloud SQL instance IP address"
  value       = google_sql_database_instance.main.ip_address[0].ip_address
}

output "cloud_sql_instance_private_ip_address" {
  description = "Cloud SQL instance private IP address"
  value       = google_sql_database_instance.main.private_ip_address
}

# Artifact Registry
output "dagster_artifact_registry_repository_url" {
  description = "Dagster Artifact Registry repository URL"
  value       = google_artifact_registry_repository.dagster.id
}

output "dagster_artifact_registry_repository_name" {
  description = "Dagster Artifact Registry repository name"
  value       = google_artifact_registry_repository.dagster.name
}

output "dagster_artifact_registry_image_url" {
  description = "Dagster Artifact Registry image URL for Cloud Run"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.dagster.repository_id}/dagster"
}

output "user_code_artifact_registry_repository_url" {
  description = "User code Artifact Registry repository URL"
  value       = google_artifact_registry_repository.user_code.id
}

output "user_code_artifact_registry_repository_name" {
  description = "User code Artifact Registry repository name"
  value       = google_artifact_registry_repository.user_code.name
}

output "user_code_artifact_registry_image_url" {
  description = "User code Artifact Registry image URL for Cloud Run"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.user_code.repository_id}/user-code"
}

# IAM Service Accounts
output "task_service_account_email" {
  description = "Task service account email"
  value       = google_service_account.task.email
}

output "task_service_account_id" {
  description = "Task service account ID"
  value       = google_service_account.task.id
}

output "execution_service_account_email" {
  description = "Execution service account email"
  value       = google_service_account.execution.email
}

output "execution_service_account_id" {
  description = "Execution service account ID"
  value       = google_service_account.execution.id
}

output "bigquery_service_account_email" {
  description = "BigQuery DBT service account email"
  value       = google_service_account.bigquery.email
}

output "bigquery_service_account_id" {
  description = "BigQuery DBT service account ID"
  value       = google_service_account.bigquery.id
}

# Secret Manager - Individual secret outputs
output "dagster_postgres_db_name_secret_id" {
  description = "Dagster PostgreSQL database name secret ID"
  value       = google_secret_manager_secret.dagster_postgres_db_name.secret_id
}

output "dagster_postgres_username_secret_id" {
  description = "Dagster PostgreSQL username secret ID"
  value       = google_secret_manager_secret.dagster_postgres_username.secret_id
}

output "dagster_postgres_password_secret_id" {
  description = "Dagster PostgreSQL password secret ID"
  value       = google_secret_manager_secret.dagster_postgres_password.secret_id
}

output "dbt_bigquery_keyfile_secret_id" {
  description = "DBT BigQuery keyfile secret ID"
  value       = google_secret_manager_secret.dbt_bigquery_keyfile.secret_id
}

output "dbt_bigquery_project_secret_id" {
  description = "DBT BigQuery project secret ID"
  value       = google_secret_manager_secret.dbt_bigquery_project.secret_id
}

output "dbt_bigquery_dataset_secret_id" {
  description = "DBT BigQuery dataset secret ID"
  value       = var.dbt_env_secret_bigquery_dataset != "" ? google_secret_manager_secret.dbt_bigquery_dataset[0].secret_id : null
}

output "dbt_bigquery_location_secret_id" {
  description = "DBT BigQuery location secret ID"
  value       = google_secret_manager_secret.dbt_bigquery_location.secret_id
}

# BigQuery Datasets
output "bigquery_datasets" {
  description = "Map of BigQuery dataset IDs created for DBT"
  value = {
    for k, v in google_bigquery_dataset.dbt : k => {
      dataset_id = v.dataset_id
      project    = v.project
      location   = v.location
    }
  }
}

output "bigquery_dataset_ids" {
  description = "List of BigQuery dataset IDs created for DBT"
  value       = [for k, v in google_bigquery_dataset.dbt : v.dataset_id]
}

# Legacy BigQuery Dataset (for backward compatibility)
output "bigquery_dataset_id" {
  description = "BigQuery dataset ID (legacy)"
  value       = var.dbt_env_secret_bigquery_dataset != "" ? google_bigquery_dataset.main[0].dataset_id : null
}

output "bigquery_dataset_project" {
  description = "BigQuery dataset project (legacy)"
  value       = var.dbt_env_secret_bigquery_dataset != "" ? google_bigquery_dataset.main[0].project : null
}