resource "google_service_account" "data_pipeline" {
  account_id   = "${var.resource_prefix}-data-pipeline"
  display_name = "Data Pipeline Service Account"
  description  = "データパイプライン実行用サービスアカウント"
}

