# Get available zones
data "google_compute_zones" "available" {
  region = var.region
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "${var.prefix}-vpc"
  auto_create_subnetworks = false
}

# Public Subnets
resource "google_compute_subnetwork" "public" {
  count         = length(var.public_subnet_cidrs)
  name          = "${var.prefix}-public-subnet-${count.index + 1}"
  ip_cidr_range = var.public_subnet_cidrs[count.index]
  region        = var.region
  network       = google_compute_network.main.id
}

# Private Subnets
resource "google_compute_subnetwork" "private" {
  count                    = length(var.private_subnet_cidrs)
  name                     = "${var.prefix}-private-subnet-${count.index + 1}"
  ip_cidr_range            = var.private_subnet_cidrs[count.index]
  region                   = var.region
  network                  = google_compute_network.main.id
  private_ip_google_access = true
}

# Cloud Router for NAT
resource "google_compute_router" "main" {
  name    = "${var.prefix}-router"
  region  = var.region
  network = google_compute_network.main.id
}

# Cloud NAT for private subnet internet access
resource "google_compute_router_nat" "main" {
  name                               = "${var.prefix}-nat"
  router                             = google_compute_router.main.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  subnetwork {
    name                    = google_compute_subnetwork.private[0].id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
}

# Firewall Rules
resource "google_compute_firewall" "alb" {
  name        = "${var.prefix}-alb-firewall"
  network     = google_compute_network.main.name
  description = "Allow HTTP/HTTPS traffic to ALB"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = length(var.prefix_list_ids) > 0 ? var.prefix_list_ids : ["0.0.0.0/0"]
  target_tags   = ["alb"]
}

resource "google_compute_firewall" "web" {
  name        = "${var.prefix}-web-firewall"
  network     = google_compute_network.main.name
  description = "Allow HTTP/HTTPS traffic from ALB"

  allow {
    protocol = "tcp"
    ports    = ["3000"]
  }

  source_tags = ["alb"]
  target_tags = ["web"]
}

resource "google_compute_firewall" "daemon" {
  name        = "${var.prefix}-daemon-firewall"
  network     = google_compute_network.main.name
  description = "Allow outbound traffic from daemon"

  allow {
    protocol = "tcp"
  }

  allow {
    protocol = "udp"
  }

  allow {
    protocol = "icmp"
  }

  source_tags        = ["daemon"]
  destination_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "user_code" {
  name        = "${var.prefix}-user-code-firewall"
  network     = google_compute_network.main.name
  description = "Allow traffic to user code from web and daemon"

  allow {
    protocol = "tcp"
    ports    = ["4000"]
  }

  source_tags = ["web", "daemon"]
  target_tags = ["user-code"]
}

resource "google_compute_firewall" "cloud_sql" {
  name        = "${var.prefix}-cloud-sql-firewall"
  network     = google_compute_network.main.name
  description = "Allow PostgreSQL from web, daemon, and user-code"

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  source_tags = ["web", "daemon", "user-code"]
  target_tags = ["cloud-sql"]
}

# Private Service Connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.prefix}-private-ip-address"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 24
  network       = google_compute_network.main.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
  depends_on              = [google_compute_global_address.private_ip_address]
}

# Cloud SQL
resource "google_sql_database_instance" "main" {
  name             = "${var.prefix}-dagster-db"
  database_version = "POSTGRES_15"
  region           = var.region
  project          = var.project_id

  settings {
    tier              = "db-custom-2-4096"
    disk_size         = 20
    disk_type         = "PD_SSD"
    disk_autoresize   = false
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.main.self_link
    }

    backup_configuration {
      enabled = false
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  deletion_protection = false

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

# データベース削除前のクリーンアップリソース
# 注意: このリソースは削除時にデータベース内のオブジェクトをクリーンアップするためのものです
# 実際のクリーンアップは、applicationレイヤーを先に削除することで行います
# 
# 削除手順:
# 1. applicationレイヤー（terraform/application）を先に削除: terraform destroy
# 2. foundationレイヤー（terraform/foundation）を削除: terraform destroy
#    この際、データベース内のオブジェクトが自動的に削除されます
resource "null_resource" "database_cleanup" {
  # このリソースは削除時にのみ実行されます
  triggers = {
    database_name = var.dagster_postgres_db
    instance_name = google_sql_database_instance.main.name
  }

  lifecycle {
    create_before_destroy = false
  }
}

resource "google_sql_database" "main" {
  name     = var.dagster_postgres_db
  instance = google_sql_database_instance.main.name
  project  = var.project_id

  lifecycle {
    # データベースを削除する前に、すべての接続を切断し、オブジェクトを削除する必要がある
    # applicationレイヤー（Cloud Runサービス）を先に削除してください
    create_before_destroy = false
  }

  depends_on = [null_resource.database_cleanup]
}

# Generate random password for PostgreSQL
resource "random_password" "dagster_postgres_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "google_sql_user" "main" {
  name     = var.dagster_postgres_user
  password = random_password.dagster_postgres_password.result
  instance = google_sql_database_instance.main.name
  project  = var.project_id

  lifecycle {
    # 削除順序を制御するため、データベースを先に削除してからユーザーを削除する
    # PostgreSQLでは、データベースを削除すると、その中のすべてのオブジェクトも自動的に削除される
    # そのため、データベースを削除してからユーザーを削除する必要がある
    # 
    # 削除手順:
    # 1. applicationレイヤー（Cloud Runサービス）を先に削除して接続を切断
    # 2. データベースを削除（データベースを削除すると、その中のオブジェクトも自動的に削除される）
    # 3. ユーザーを削除
    create_before_destroy = false
  }

  # ユーザーがデータベースに依存することで、削除時にデータベースが先に削除される
  # Terraformは削除時に依存関係を逆順で処理するため、
  # ユーザーがデータベースに依存している場合、削除時にデータベースが先に削除される
  depends_on = [google_sql_database.main]
}

# Artifact Registry
resource "google_artifact_registry_repository" "dagster" {
  location      = var.region
  repository_id = "${var.prefix}-dagster-cloudrun-core"
  description   = "Dagster Cloud Run core container repository"
  format        = "DOCKER"
  project       = var.project_id
}

resource "google_artifact_registry_repository" "user_code" {
  location      = var.region
  repository_id = "${var.prefix}-dagster-cloudrun-user-code"
  description   = "Dagster Cloud Run user code container repository"
  format        = "DOCKER"
  project       = var.project_id
}

# Service Accounts
resource "google_service_account" "task" {
  account_id   = "${var.prefix}-dagster-task"
  display_name = "Dagster Cloud Run Task Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "task_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.task.email}"
}

resource "google_project_iam_member" "task_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.task.email}"
}

resource "google_project_iam_member" "task_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.user"
  member  = "serviceAccount:${google_service_account.task.email}"
}

resource "google_project_iam_member" "task_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.task.email}"
}

resource "google_service_account" "execution" {
  account_id   = "${var.prefix}-dagster-execution"
  display_name = "Dagster Cloud Run Execution Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "execution_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.execution.email}"
}

resource "google_project_iam_member" "execution_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.execution.email}"
}

resource "google_project_iam_member" "execution_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.execution.email}"
}

# BigQuery Service Account for DBT
resource "google_service_account" "bigquery" {
  account_id   = "${var.prefix}-bigquery-dbt"
  display_name = "BigQuery DBT Service Account"
  project      = var.project_id
}

# BigQuery Service Account IAM
resource "google_project_iam_member" "bigquery_bigquery_user" {
  project = var.project_id
  role    = "roles/bigquery.user"
  member  = "serviceAccount:${google_service_account.bigquery.email}"
}

resource "google_project_iam_member" "bigquery_bigquery_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.bigquery.email}"
}

resource "google_project_iam_member" "bigquery_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.bigquery.email}"
}

resource "google_project_iam_member" "bigquery_bigquery_data_owner" {
  project = var.project_id
  role    = "roles/bigquery.dataOwner"
  member  = "serviceAccount:${google_service_account.bigquery.email}"
}

# Generate service account key for BigQuery
resource "google_service_account_key" "bigquery" {
  service_account_id = google_service_account.bigquery.name
}

# Secret Manager - Individual secrets for Cloud Run
# Each environment variable needs its own secret in Cloud Run

# Dagster PostgreSQL secrets
resource "google_secret_manager_secret" "dagster_postgres_db_name" {
  secret_id = "${var.prefix}-dagster-postgres-db-name"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dagster_postgres_db_name" {
  secret      = google_secret_manager_secret.dagster_postgres_db_name.id
  secret_data = var.dagster_postgres_db
}

resource "google_secret_manager_secret" "dagster_postgres_username" {
  secret_id = "${var.prefix}-dagster-postgres-username"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dagster_postgres_username" {
  secret      = google_secret_manager_secret.dagster_postgres_username.id
  secret_data = var.dagster_postgres_user
}

resource "google_secret_manager_secret" "dagster_postgres_password" {
  secret_id = "${var.prefix}-dagster-postgres-password"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dagster_postgres_password" {
  secret      = google_secret_manager_secret.dagster_postgres_password.id
  secret_data = random_password.dagster_postgres_password.result
}

# DBT BigQuery secrets
resource "google_secret_manager_secret" "dbt_bigquery_keyfile" {
  secret_id = "${var.prefix}-dbt-env-secret-bigquery-keyfile"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dbt_bigquery_keyfile" {
  secret      = google_secret_manager_secret.dbt_bigquery_keyfile.id
  secret_data = base64decode(google_service_account_key.bigquery.private_key)
}

resource "google_secret_manager_secret" "dbt_bigquery_project" {
  secret_id = "${var.prefix}-dbt-env-secret-bigquery-project"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dbt_bigquery_project" {
  secret      = google_secret_manager_secret.dbt_bigquery_project.id
  secret_data = var.dbt_env_secret_bigquery_project
}

resource "google_secret_manager_secret" "dbt_bigquery_dataset" {
  count      = var.dbt_env_secret_bigquery_dataset != "" ? 1 : 0
  secret_id  = "${var.prefix}-dbt-env-secret-bigquery-dataset"
  project    = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dbt_bigquery_dataset" {
  count       = var.dbt_env_secret_bigquery_dataset != "" ? 1 : 0
  secret      = google_secret_manager_secret.dbt_bigquery_dataset[0].id
  secret_data = var.dbt_env_secret_bigquery_dataset
}

resource "google_secret_manager_secret" "dbt_bigquery_location" {
  secret_id = "${var.prefix}-dbt-env-secret-bigquery-location"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "dbt_bigquery_location" {
  secret      = google_secret_manager_secret.dbt_bigquery_location.id
  secret_data = var.dbt_env_secret_bigquery_location
}

# BigQuery Datasets for DBT (environment x directory combinations)
resource "google_bigquery_dataset" "dbt" {
  for_each = {
    for combo in flatten([
      for env in var.dbt_environments : [
        for dir in var.dbt_model_directories : {
          key        = "${env}_${dir}"
          dataset_id = "${var.dataset_prefix}_${env}_${dir}"
          env        = env
          dir        = dir
        }
      ]
    ]) : combo.key => combo
  }

  dataset_id  = each.value.dataset_id
  project     = var.project_id
  location    = var.dbt_env_secret_bigquery_location
  description = "BigQuery dataset for DBT ${each.value.env} environment - ${each.value.dir} models"

  labels = {
    managed_by  = "terraform"
    prefix      = var.prefix
    environment = each.value.env
    directory   = each.value.dir
  }

  access {
    role          = "OWNER"
    user_by_email = google_service_account.bigquery.email
  }
}

# Legacy BigQuery Dataset (for backward compatibility)
resource "google_bigquery_dataset" "main" {
  count       = var.dbt_env_secret_bigquery_dataset != "" ? 1 : 0
  dataset_id  = var.dbt_env_secret_bigquery_dataset
  project     = var.project_id
  location    = var.dbt_env_secret_bigquery_location
  description = "BigQuery dataset for DBT transformations (legacy)"

  labels = {
    managed_by = "terraform"
    prefix     = var.prefix
  }

  access {
    role          = "OWNER"
    user_by_email = google_service_account.bigquery.email
  }
}
