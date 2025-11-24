resource "google_bigquery_dataset" "data_lake" {
  dataset_id = "data_lake"
  location   = "US"
  project    = var.project_id

  labels = local.common_labels

  description = "Data lake dataset for raw data storage"
}

