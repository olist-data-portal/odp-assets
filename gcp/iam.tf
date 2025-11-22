# GCSバケットへのアクセス権限
resource "google_storage_bucket_iam_member" "data_pipeline_gcs_reader" {
  bucket = google_storage_bucket.data_lake.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.data_pipeline.email}"
}

resource "google_storage_bucket_iam_member" "data_pipeline_gcs_writer" {
  bucket = google_storage_bucket.data_lake.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.data_pipeline.email}"
}

# インフラリポジトリで作成されたサービスアカウントを参照
data "google_service_account" "task" {
  account_id = "odp-dagster-task-sa-${var.environment}"
  project    = var.project_id
}

# BigQuery関連のIAMロールを付与
resource "google_project_iam_member" "task_bigquery_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${data.google_service_account.task.email}"
}

resource "google_project_iam_member" "task_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${data.google_service_account.task.email}"
}

