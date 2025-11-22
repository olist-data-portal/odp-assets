output "service_account_email" {
  description = "データパイプライン実行用サービスアカウントのメールアドレス"
  value       = google_service_account.data_pipeline.email
}

output "gcs_bucket_name" {
  description = "GCSバケット名"
  value       = google_storage_bucket.data_lake.name
}

