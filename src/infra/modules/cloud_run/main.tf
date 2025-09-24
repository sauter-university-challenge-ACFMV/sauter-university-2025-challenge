resource "google_cloud_run_v2_service" "svc" {
  name     = var.name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  labels = {
    env     = var.env
    service = "ml-api"
    owner   = "adenilson-clauderson-raylandson"
  }

  template {
    service_account = var.service_account_email
    
    containers {
      image = var.image
      
      dynamic "env" {
        for_each = var.secret_environment_variables
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_name
              version = env.value.secret_version
            }
          }
        }
      }
    }
  }

  # Tráfego para rollback (Caso der um problema na nova versão)
  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  # Permite GitHub Actions gerenciar tráfego 
  lifecycle {
    ignore_changes = [
      traffic
    ]
  }
}