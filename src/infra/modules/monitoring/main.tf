resource "google_monitoring_alert_policy" "error_5xx_alert" {
  display_name = "API 5xx Error Rate Alert"
  combiner     = "OR"
  enabled      = true
  notification_channels = [google_monitoring_notification_channel.budget_email.id]

  conditions {
    display_name = "5xx Errors > 0"
    condition_threshold {
      filter = "metric.type=\"run.googleapis.com/request/count\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.service_name}\" metric.label.response_code_class=\"5xx\""
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
      }
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "300s" # 5 minutos
      trigger {
        count = 1
      }
    }
  }

  alert_strategy {
    auto_close = "300s"
  }
}



resource "google_monitoring_alert_policy" "latency_alert" {
  display_name = "API Latency Alert"
  combiner     = "OR"
  enabled      = true
  notification_channels = [google_monitoring_notification_channel.budget_email.id]

  conditions {
    display_name = "High Latency (p95 > 500ms)"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request/latencies\" resource.type=\"cloud_run_revision\" resource.label.service_name=\"${var.service_name}\""
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
      }
      comparison      = "COMPARISON_GT"
      threshold_value = 500000000
      duration        = "300s" 
      trigger {
        count = 1
      }
    }
  }
  alert_strategy {
    auto_close = "300s" 
  }
}


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
      columns = 24  
      tiles = [{
        width  = 12
        height = 4
        widget = {
          title = "API Latency (p95)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/request/latencies\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.service_name}\""
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
      }, {
        width  = 12
        height = 4
        yPos   = 4
        widget = {
          title = "API Error Rate (5xx)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/request/count\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.service_name}\" metric.label.response_code_class=\"5xx\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_RATE"
                    crossSeriesReducer = "REDUCE_SUM"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Errors per second"
            }
          }
        }
      }, {
        width  = 12
        height = 4
        yPos   = 8
        widget = {
          title = "API Queries per Second (QPS)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"run.googleapis.com/request/count\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.service_name}\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_RATE"
                    crossSeriesReducer = "REDUCE_SUM"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Requests per second"
            }
          }
        }
      }, {
        width  = 12
        height = 4
        yPos   = 12
        widget = {
          title = "Daily Cost"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"billing.googleapis.com/billing_account/current_month/cost\" resource.type=\"cloud_run_revision\" metric.label.currency=\"BRL\" resource.labels.service_name=\"${var.service_name}\""
                  aggregation = {
                    alignmentPeriod    = "86400s"
                    perSeriesAligner   = "ALIGN_SUM"
                    crossSeriesReducer = "REDUCE_SUM"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "BRL per day"
            }
          }
        }
      }, {
        width  = 12
        height = 4
        yPos   = 16
        widget = {
          title = "API Log-Based Server Errors"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "metric.type=\"logging.googleapis.com/user/api-server-errors\" resource.type=\"cloud_run_revision\" resource.labels.service_name=\"${var.service_name}\""
                  aggregation = {
                    alignmentPeriod    = "300s"
                    perSeriesAligner   = "ALIGN_SUM"
                    crossSeriesReducer = "REDUCE_SUM"
                  }
                }
              }
              plotType = "LINE"
            }]
            yAxis = {
              label = "Errors (5 min)"
            }
          }
        }
      }]
    }
  })
}
