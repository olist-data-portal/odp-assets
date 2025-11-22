resource "google_storage_bucket" "data_lake" {
  name                        = "${var.resource_prefix}-data-lake"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  labels = local.common_labels

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}

