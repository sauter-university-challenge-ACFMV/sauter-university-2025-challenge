resource "google_monitoring_notification_channel" "budget_email" {
  project      = var.project_id
  display_name = "Budget Alerts"
  type         = "email"
  labels = {
    email_address = var.group_email
  }
}
