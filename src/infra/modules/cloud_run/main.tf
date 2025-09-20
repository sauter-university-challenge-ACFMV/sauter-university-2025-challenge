resource "google_cloud_run_v2_service" "svc" {
  name     = var.name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.service_account_email
    containers {
      image = var.image
      # opcional: port 8080 é o padrão do hello container
    }
  }
}

# Tornar público (invocável sem auth) se desejado
resource "google_cloud_run_v2_service_iam_binding" "invoker_all" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.svc.name
  location = var.region
  role     = "roles/run.invoker"
  members  = ["allUsers"]
}
