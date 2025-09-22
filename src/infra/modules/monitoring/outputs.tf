output "channel_id" {
  value = google_monitoring_notification_channel.budget_email.name
}

output "dashboard_url" {
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.api_health.id}?project=${var.project_id}"
  description = "URL do dashboard de monitoramento da API"
}
