output "url" {
  value = google_cloud_run_v2_service.svc.uri 
}

output "service_name" { value = google_cloud_run_v2_service.svc.name }
output "service_id" { value = google_cloud_run_v2_service.svc.id }
output "latest_ready_revision" { value = google_cloud_run_v2_service.svc.latest_ready_revision }
output "location" { value = google_cloud_run_v2_service.svc.location }