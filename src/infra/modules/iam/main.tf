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
    "roles/serviceusage.serviceUsageAdmin",  # habilitar APIs via Terraform
    "roles/storage.admin",                   # criar buckets / lifecycle
    "roles/artifactregistry.admin",          # criar repo e gerenciar
    "roles/run.admin",                       # criar/atualizar Cloud Run
    "roles/bigquery.admin",                  # criar datasets/tables
    "roles/secretmanager.admin",             # criar segredos e bindings
    "roles/logging.configWriter",            # Create log sinks and metrics
    "roles/monitoring.alertPolicyEditor",    # Create alert policies
  ])
  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.terraform.email}"
}


# Allow Terraform to **use** the runtime SA when configuring Cloud Run
resource "google_service_account_iam_member" "tf_can_use_runtime_sa" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.terraform.email}"
}

# At runtime, Cloud Run needs to read images from Artifact Registry
resource "google_project_iam_member" "runtime_artifact_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}
