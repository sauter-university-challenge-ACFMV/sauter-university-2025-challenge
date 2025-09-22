resource "google_cloud_run_v2_service" "svc" {
	name     = var.name
	location = var.region
	ingress  = "INGRESS_TRAFFIC_ALL"

  labels = {
    env     = var.env
    service = "ml-api"
    owner   = "adenilson-clauderson"
  }

  template {
    service_account = var.service_account_email
    containers {
      image = var.image
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

resource "google_cloud_run_v2_service_iam_binding" "invoker_all" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.svc.name
  location = var.region
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}
