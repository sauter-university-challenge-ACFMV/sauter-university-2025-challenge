resource "google_monitoring_notification_channel" "budget_email" {
  project      = var.project_id
  display_name = "Budget Alerts"
  type         = "email"
  labels = {
    email_address = var.group_email
  }
}

resource "google_monitoring_dashboard" "api_health" {
  project        = var.project_id
  dashboard_json = jsonencode({
    displayName = "API Health Dashboard"
    mosaicLayout = {
      tiles = [{
        width  = 12
        height = 4
        widget = {
          title = "API Latency (p95)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/request/latencies\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.service_name}\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_DELTA"
                    crossSeriesReducer = "REDUCE_PERCENTILE_95"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Latency (ms)"
            }
          }
        }
      }]
    }
  })
}
