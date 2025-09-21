resource "google_billing_budget" "this" {
  billing_account = var.billing_account
  display_name    = "dev-monthly-budget"

  amount {
    specified_amount {
      currency_code = var.currency_code
      units         = tostring(var.amount)
    }
  }

  threshold_rules { threshold_percent = 0.5 }
  threshold_rules { threshold_percent = 0.9 }
  threshold_rules { threshold_percent = 1.0 }

  budget_filter {
    projects = ["projects/${var.project_number}"]
  }

    dynamic "all_updates_rule" {
    for_each = length(var.monitoring_channel_ids) > 0 ? [1] : []
    content {
        monitoring_notification_channels = var.monitoring_channel_ids
        enable_project_level_recipients  = true
        }
    }

}
