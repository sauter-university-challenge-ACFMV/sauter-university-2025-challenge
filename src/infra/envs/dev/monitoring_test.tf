# Uptime check que SEMPRE falha
resource "google_monitoring_uptime_check_config" "fail_check" {
  display_name = "TEST - Always fail"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path = "/"
    port = 80
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = "10.255.255.1"   # não roteável => falha
    }
  }
}

# Policy que dispara no canal de e-mail do grupo
# mantém seu uptime check como está
resource "google_monitoring_alert_policy" "test_email" {
  display_name = "TEST - Email channel fires"
  combiner     = "OR"
  notification_channels = [module.monitoring.channel_id]

  documentation {
    content   = "Teste de notificação por e-mail. Pode ignorar."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Uptime check failing"
    condition_threshold {
      # check_passed: 1 = passou; 0 = falhou
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" resource.type=\"uptime_url\" metric.label.\"check_id\"=\"${google_monitoring_uptime_check_config.fail_check.uptime_check_id}\""
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      duration        = "60s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_NEXT_OLDER"
      }
    }
  }
}

