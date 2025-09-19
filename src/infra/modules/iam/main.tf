# Service Accounts
resource "google_service_account" "terraform" {
  account_id   = "terraform-deployer"
  display_name = "Terraform Deployer"
}

resource "google_service_account" "runtime" {
  account_id   = "cloud-run-runtime"
  display_name = "Cloud Run Runtime"
}

# Papéis do Terraform SA
resource "google_project_iam_member" "tf_roles" {
  for_each = toset([
    "roles/viewer",
    "roles/storage.admin",
    "roles/artifactregistry.admin",
    "roles/run.admin",
    "roles/bigquery.admin",
    "roles/secretmanager.admin",
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.terraform.email}"
}

# Permitir que o Terraform **use** a runtime SA ao configurar Cloud Run
resource "google_service_account_iam_member" "tf_can_use_runtime_sa" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.terraform.email}"
}

# Em runtime, o Cloud Run precisa ler imagens do Artifact Registry
resource "google_project_iam_member" "runtime_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}
