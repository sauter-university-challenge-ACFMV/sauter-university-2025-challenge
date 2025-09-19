resource "google_iam_workload_identity_pool" "pool" {
  project                   = var.project_id
  workload_identity_pool_id = var.pool_id
  display_name              = "GitHub OIDC Pool"
}

resource "google_iam_workload_identity_pool_provider" "provider" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  display_name                       = "GitHub Provider"

  oidc { issuer_uri = "https://token.actions.githubusercontent.com" }

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
    "attribute.actor"      = "assertion.actor"
    "attribute.workflow"   = "assertion.workflow"
  }

  # restrição explícita usando o atributo que você mapeou
  attribute_condition = "attribute.repository == \"${var.github_repo}\""
}


# Permite que o repositório GitHub assuma a SA via principalSet
resource "google_service_account_iam_binding" "wif_user" {
  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.sa_email}"
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.pool.name}/attribute.repository/${var.github_repo}"
  ]
}
