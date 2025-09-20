resource "google_artifact_registry_repository" "docker" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repo_id
  format        = "DOCKER"
  description   = "Docker images for Cloud Run"
}
