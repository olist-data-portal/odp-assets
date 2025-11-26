resource "google_bigquery_dataset" "data_lake" {
  dataset_id = "data_lake"
  location   = "US"
  project    = var.project_id

  labels = local.common_labels

  description = "Data lake dataset for raw data storage"
}

# dbt用データセット（prd環境）
resource "google_bigquery_dataset" "odp_staging" {
  count = var.environment == "prd" ? 1 : 0

  dataset_id = "staging"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt staging layer dataset"
}

resource "google_bigquery_dataset" "odp_intermediate" {
  count = var.environment == "prd" ? 1 : 0

  dataset_id = "intermediate"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt intermediate layer dataset"
}

resource "google_bigquery_dataset" "odp_warehouse" {
  count = var.environment == "prd" ? 1 : 0

  dataset_id = "warehouse"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt warehouse layer dataset"
}

resource "google_bigquery_dataset" "odp_mart" {
  count = var.environment == "prd" ? 1 : 0

  dataset_id = "mart"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt mart layer dataset"
}

# dbt用データセット（stg環境）
resource "google_bigquery_dataset" "odp_stg_staging" {
  count = var.environment != "prd" ? 1 : 0

  dataset_id = "odp-stg-staging"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt staging layer dataset (stg environment)"
}

resource "google_bigquery_dataset" "odp_stg_intermediate" {
  count = var.environment != "prd" ? 1 : 0

  dataset_id = "odp-stg-intermediate"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt intermediate layer dataset (stg environment)"
}

resource "google_bigquery_dataset" "odp_stg_warehouse" {
  count = var.environment != "prd" ? 1 : 0

  dataset_id = "odp-stg-warehouse"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt warehouse layer dataset (stg environment)"
}

resource "google_bigquery_dataset" "odp_stg_mart" {
  count = var.environment != "prd" ? 1 : 0

  dataset_id = "odp-stg-mart"
  location   = "asia-northeast1"
  project    = var.project_id

  labels = local.common_labels

  description = "dbt mart layer dataset (stg environment)"
}

