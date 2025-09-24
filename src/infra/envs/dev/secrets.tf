# src/infra/envs/dev/secrets.tf

# =========================================================
# 1. DECLARAR AS VARIÁVEIS QUE RECEBERÃO OS VALORES
#    Esses valores virão do GitHub Actions
# =========================================================
variable "ons_api_url" {
  type        = string
  description = "URL da API da ONS."
  sensitive   = true
}

variable "gcs_bucket_name" {
  type        = string
  description = "Nome do bucket GCS para a aplicação."
  sensitive   = true
}


resource "google_secret_manager_secret" "ons_api_url" {
  project   = var.project_id
  secret_id = "ons-api-url" # Nome do segredo no GCP

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "gcs_bucket_name" {
  project   = var.project_id
  secret_id = "gcs-bucket-name" # Nome do segredo no GCP

  replication {
    auto {}
  }
}


resource "google_secret_manager_secret_version" "ons_api_url_version" {
  secret      = google_secret_manager_secret.ons_api_url.id
  secret_data = var.ons_api_url
}

resource "google_secret_manager_secret_version" "gcs_bucket_name_version" {
  secret      = google_secret_manager_secret.gcs_bucket_name.id
  secret_data = var.gcs_bucket_name
}


resource "google_secret_manager_secret_iam_member" "ons_api_url_accessor" {
  project   = google_secret_manager_secret.ons_api_url.project
  secret_id = google_secret_manager_secret.ons_api_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.iam.runtime_sa_email}"
}

resource "google_secret_manager_secret_iam_member" "gcs_bucket_name_accessor" {
  project   = google_secret_manager_secret.gcs_bucket_name.project
  secret_id = google_secret_manager_secret.gcs_bucket_name.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${module.iam.runtime_sa_email}"
}