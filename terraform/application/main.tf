# Data sources to reference foundation outputs
data "terraform_remote_state" "foundation" {
    backend = "local"
    config = {
        path = "../foundation/terraform.tfstate"
    }
}

# Cloud Load Balancer
resource "google_compute_health_check" "web" {
    name = "${var.prefix}-dagster-web-health-check"
    check_interval_sec = 30
    timeout_sec = 5
    healthy_threshold = 2
    unhealthy_threshold = 2

    http_health_check {
        port = 3000
        request_path = "/"
    }
}

resource "google_compute_url_map" "main" {
    name = "${var.prefix}-dagster-url-map"
    default_service = google_compute_backend_service.web.id
}

resource "google_compute_target_http_proxy" "main" {
    name = "${var.prefix}-dagster-http-proxy"
    url_map = google_compute_url_map.main.id
}

resource "google_compute_global_forwarding_rule" "main" {
    name = "${var.prefix}-dagster-forwarding-rule"
    target = google_compute_target_http_proxy.main.id
    port_range = "80"
    ip_protocol = "TCP"
}

# Cloud Run Services
resource "google_cloud_run_service" "web" {
    name = "${var.prefix}-dagster-web"
    location = var.region
    project = var.project_id

    template {
        spec {
            containers {
                image = "${data.terraform_remote_state.foundation.outputs.dagster_artifact_registry_image_url}:latest"
                args = ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]

                ports {
                    container_port = 3000
                }

                env {
                    name = "DAGSTER_POSTGRES_HOST"
                    value = data.terraform_remote_state.foundation.outputs.cloud_sql_instance_private_ip_address
                }

                env {
                    name = "DAGSTER_POSTGRES_DB"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_db_name_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DAGSTER_POSTGRES_USER"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_username_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DAGSTER_POSTGRES_PASSWORD"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_password_secret_id
                            key  = "latest"
                        }
                    }
                }

                # Workspace.yaml selection and gRPC server configuration
                env {
                    name = "GCP_PROJECT_ID"
                    value = var.project_id
                }

                env {
                    name = "DAGSTER_USER_CODE_SERVICE"
                    value = "${var.prefix}-dagster-user-code"
                }

                resources {
                    limits = {
                        cpu = "1"
                        memory = "1Gi"
                    }
                }
            }

            service_account_name = data.terraform_remote_state.foundation.outputs.task_service_account_email
        }

        metadata {
            annotations = {
                "run.googleapis.com/cloudsql-instances" = data.terraform_remote_state.foundation.outputs.cloud_sql_instance_connection_name
                "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.main.name
                "run.googleapis.com/vpc-access-egress" = "private-ranges-only"
            }
        }
    }

    traffic {
        percent = 100
        latest_revision = true
    }
}

resource "google_cloud_run_service_iam_member" "web_public" {
    service = google_cloud_run_service.web.name
    location = google_cloud_run_service.web.location
    role = "roles/run.invoker"
    member = "allUsers"
}

resource "google_cloud_run_service" "daemon" {
    name = "${var.prefix}-dagster-daemon"
    location = var.region
    project = var.project_id

    template {
        spec {
            containers {
                image = "${data.terraform_remote_state.foundation.outputs.dagster_artifact_registry_image_url}:latest"
                command = ["sh", "-c"]
                args = ["dagster-daemon run & python -m http.server 8080"]

                ports {
                    container_port = 8080
                }

                env {
                    name = "DAGSTER_POSTGRES_HOST"
                    value = data.terraform_remote_state.foundation.outputs.cloud_sql_instance_private_ip_address
                }

                env {
                    name = "DAGSTER_POSTGRES_DB"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_db_name_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DAGSTER_POSTGRES_USER"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_username_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DAGSTER_POSTGRES_PASSWORD"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_password_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DBT_ENV_SECRET_BIGQUERY_KEYFILE"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_keyfile_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DBT_ENV_SECRET_BIGQUERY_PROJECT"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_project_secret_id
                            key  = "latest"
                        }
                    }
                }

                dynamic "env" {
                    for_each = try(data.terraform_remote_state.foundation.outputs.dbt_bigquery_dataset_secret_id, null) != null ? [1] : []
                    content {
                        name = "DBT_ENV_SECRET_BIGQUERY_DATASET"
                        value_from {
                            secret_key_ref {
                                name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_dataset_secret_id
                                key  = "latest"
                            }
                        }
                    }
                }

                env {
                    name = "DBT_ENV_SECRET_BIGQUERY_LOCATION"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_location_secret_id
                            key  = "latest"
                        }
                    }
                }

                # Workspace.yaml selection and gRPC server configuration
                env {
                    name = "GCP_PROJECT_ID"
                    value = var.project_id
                }

                env {
                    name = "DAGSTER_USER_CODE_SERVICE"
                    value = "${var.prefix}-dagster-user-code"
                }

                resources {
                    limits = {
                        cpu = "1"
                        memory = "1Gi"
                    }
                }
            }

            service_account_name = data.terraform_remote_state.foundation.outputs.task_service_account_email
        }

        metadata {
            annotations = {
                "run.googleapis.com/cloudsql-instances" = data.terraform_remote_state.foundation.outputs.cloud_sql_instance_connection_name
                "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.main.name
                "run.googleapis.com/vpc-access-egress" = "private-ranges-only"
            }
        }
    }

    traffic {
        percent = 100
        latest_revision = true
    }
}

resource "google_cloud_run_service" "user_code" {
    name = "${var.prefix}-dagster-user-code"
    location = var.region
    project = var.project_id

    template {
        spec {
            containers {
                image = "${data.terraform_remote_state.foundation.outputs.user_code_artifact_registry_image_url}:latest"

                ports {
                    container_port = 4000
                }

                env {
                    name = "DAGSTER_POSTGRES_HOST"
                    value = data.terraform_remote_state.foundation.outputs.cloud_sql_instance_private_ip_address
                }

                env {
                    name = "DAGSTER_CURRENT_IMAGE"
                    value = "${data.terraform_remote_state.foundation.outputs.user_code_artifact_registry_image_url}:latest"
                }

                env {
                    name = "DAGSTER_DBT_PARSE_PROJECT_ON_LOAD"
                    value = "1"
                }

                env {
                    name = "DAGSTER_POSTGRES_DB"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_db_name_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DAGSTER_POSTGRES_USER"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_username_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DAGSTER_POSTGRES_PASSWORD"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dagster_postgres_password_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DBT_ENV_SECRET_BIGQUERY_KEYFILE"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_keyfile_secret_id
                            key  = "latest"
                        }
                    }
                }

                env {
                    name = "DBT_ENV_SECRET_BIGQUERY_PROJECT"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_project_secret_id
                            key  = "latest"
                        }
                    }
                }

                dynamic "env" {
                    for_each = try(data.terraform_remote_state.foundation.outputs.dbt_bigquery_dataset_secret_id, null) != null ? [1] : []
                    content {
                        name = "DBT_ENV_SECRET_BIGQUERY_DATASET"
                        value_from {
                            secret_key_ref {
                                name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_dataset_secret_id
                                key  = "latest"
                            }
                        }
                    }
                }

                env {
                    name = "DBT_ENV_SECRET_BIGQUERY_LOCATION"
                    value_from {
                        secret_key_ref {
                            name = data.terraform_remote_state.foundation.outputs.dbt_bigquery_location_secret_id
                            key  = "latest"
                        }
                    }
                }

                resources {
                    limits = {
                        cpu = "1"
                        memory = "1Gi"
                    }
                }
            }

            service_account_name = data.terraform_remote_state.foundation.outputs.task_service_account_email
        }

        metadata {
            annotations = {
                "run.googleapis.com/cloudsql-instances" = data.terraform_remote_state.foundation.outputs.cloud_sql_instance_connection_name
                "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.main.name
                "run.googleapis.com/vpc-access-egress" = "private-ranges-only"
            }
        }
    }

    traffic {
        percent = 100
        latest_revision = true
    }
}

# VPC Access Connector for Cloud Run to access VPC resources
resource "google_vpc_access_connector" "main" {
    name = "${var.prefix}-vpc-connector"
    region = var.region
    project = var.project_id
    network = data.terraform_remote_state.foundation.outputs.vpc_name
    ip_cidr_range = "10.8.0.0/28"
    min_instances = 2
    max_instances = 3
}

# Cloud DNS for Service Discovery
resource "google_dns_managed_zone" "main" {
    name = "${var.prefix}-dagster-internal"
    dns_name = "${var.prefix}-dagster.internal."
    description = "Dagster internal DNS zone"
    project = var.project_id

    visibility = "private"

    private_visibility_config {
        networks {
            network_url = "https://www.googleapis.com/compute/v1/projects/${var.project_id}/global/networks/${data.terraform_remote_state.foundation.outputs.vpc_name}"
        }
    }
}

resource "google_dns_record_set" "user_code" {
    name = "user-code.${google_dns_managed_zone.main.dns_name}"
    type = "CNAME"
    ttl = 10
    managed_zone = google_dns_managed_zone.main.name
    project = var.project_id

    rrdatas = ["${replace(google_cloud_run_service.user_code.status[0].url, "https://", "")}."]
}

# Backend Service NEG (Network Endpoint Group) for Cloud Run
resource "google_compute_region_network_endpoint_group" "web" {
    name = "${var.prefix}-dagster-web-neg"
    network_endpoint_type = "SERVERLESS"
    region = var.region
    project = var.project_id

    cloud_run {
        service = google_cloud_run_service.web.name
    }
}

# Update backend service to use NEG
resource "google_compute_backend_service" "web" {
    name = "${var.prefix}-dagster-web-backend"
    protocol = "HTTP"
    port_name = "http"
    timeout_sec = 30
    enable_cdn = false

    backend {
        group = google_compute_region_network_endpoint_group.web.id
    }

    # Note: Serverless NEG backends cannot use health checks
    # Cloud Run services have built-in health checks

    log_config {
        enable = true
    }
}
