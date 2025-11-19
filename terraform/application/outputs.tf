# Load Balancer
output "load_balancer_ip" {
    description = "Load Balancer IP address"
    value = google_compute_global_forwarding_rule.main.ip_address
}

output "dagster_url" {
    description = "Dagster web interface URL"
    value = "http://${google_compute_global_forwarding_rule.main.ip_address}"
}

# Cloud Run
output "web_service_url" {
    description = "Cloud Run web service URL"
    value = google_cloud_run_service.web.status[0].url
}

output "daemon_service_url" {
    description = "Cloud Run daemon service URL"
    value = google_cloud_run_service.daemon.status[0].url
}

output "user_code_service_url" {
    description = "Cloud Run user code service URL"
    value = google_cloud_run_service.user_code.status[0].url
}

# Service Discovery
output "service_discovery_namespace_name" {
    description = "Service discovery namespace name"
    value = google_dns_managed_zone.main.dns_name
}

output "user_code_service_discovery_name" {
    description = "User code service discovery DNS name"
    value = google_dns_record_set.user_code.name
}
