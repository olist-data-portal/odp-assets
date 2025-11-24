output "gcs_bucket_name" {
  description = "GCSバケット名（データレイク）"
  value       = google_storage_bucket.data_lake.name
}

output "bigquery_dataset_id" {
  description = "BigQueryデータセットID（データレイク）"
  value       = google_bigquery_dataset.data_lake.dataset_id
}
