# インフラリポジトリで作成されたサービスアカウントを参照
data "google_service_account" "task" {
  account_id = "${var.resource_prefix}-dagster-task-sa-${var.environment}"
  project    = var.project_id
}

data "google_service_account" "execution" {
  account_id = "${var.resource_prefix}-dagster-exec-sa-${var.environment}"
  project    = var.project_id
}

# TaskサービスアカウントへのIAMロール付与
resource "google_project_iam_member" "task_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${data.google_service_account.task.email}"
}

resource "google_project_iam_member" "task_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${data.google_service_account.task.email}"
}

resource "google_project_iam_member" "task_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${data.google_service_account.task.email}"
}

# ExecutionサービスアカウントへのIAMロール付与
resource "google_project_iam_member" "execution_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${data.google_service_account.execution.email}"
}

resource "google_project_iam_member" "execution_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${data.google_service_account.execution.email}"
}

resource "google_project_iam_member" "execution_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${data.google_service_account.execution.email}"
}
