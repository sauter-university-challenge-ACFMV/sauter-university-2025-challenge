variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "southamerica-east1"
}

variable "bq_location" {
  type    = string
  default = "southamerica-east1"
}

variable "github_repo" {
  type = string
}

variable "dev_budget_amount" {
  type = number
}

variable "alert_group_email" {
  type = string
}

variable "gcs_bucket_name" {
  type = string
}

variable "google_credentials_json" {
  type      = string
  sensitive = true
}

variable "repo_id" {
  description = "Nome do repositório no Artifact Registry onde a imagem está armazenada"
  type        = string
}
