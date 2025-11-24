output "gcs_bucket_name" {
  description = "GCSバケット名（データレイク）"
  value       = google_storage_bucket.data_lake.name
}
