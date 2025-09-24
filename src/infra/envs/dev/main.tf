locals {
  services = [
    "artifactregistry.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "run.googleapis.com",
    "iamcredentials.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "billingbudgets.googleapis.com",
    "secretmanager.googleapis.com",
  ]
}

data "google_project" "this" {
  project_id = var.project_id
}

resource "google_project_service" "enabled" {
  for_each           = toset(local.services)
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id
}

module "wif" {
  source      = "../../modules/wif"
  project_id  = var.project_id
  pool_id     = "github"
  provider_id = "github"
  github_repo = var.github_repo
  sa_email    = module.iam.terraform_sa_email
}

module "artifact_registry" {
  source     = "../../modules/artifact_registry"
  project_id = var.project_id
  region     = var.region
  repo_id    = "apps"
}

module "cloud_run" {
  source                = "../../modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  name                  = "baseline-api"
  image                 = "us-docker.pkg.dev/cloudrun/container/hello"
  service_account_email = module.iam.runtime_sa_email
  allow_unauthenticated = true
}

module "cloud_storage" {
  source     = "../../modules/cloud_storage"
  project_id = var.project_id
  location   = var.region
  env        = "dev"
}

module "bigquery" {
  source     = "../../modules/bigquery"
  project_id = var.project_id
  location   = var.bq_location
  env        = "dev"
}

module "monitoring" {
  source      = "../../modules/monitoring"
  project_id  = var.project_id
  group_email = var.alert_group_email
}

module "budget" {
  source                 = "../../modules/budget"
  billing_account        = "012AA0-0BFB09-AC0D0F"
  project_number         = data.google_project.this.number
  amount                 = var.dev_budget_amount
  currency_code          = "BRL"
  monitoring_channel_ids = [module.monitoring.channel_id]
}

resource "google_cloud_run_service" "baseline_api" {
  name     = "baseline-api"
  location = var.region
  project  = var.project_id

  template {
    spec {
      containers {
        image = "southamerica-east1-docker.pkg.dev/${var.project_id}/${var.repo_id}/baseline-api:latest"
        ports {
          container_port = 8080
        }

        # Variáveis de ambiente (equivalente ao .env)
        env {
          name  = "ONS_API_URL"
          value = "https://dados.ons.org.br/api/3/action/package_show"
        }

        env {
          name  = "GCS_BUCKET_NAME"
          value = var.gcs_bucket_name
        }

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        # Em vez de GOOGLE_APPLICATION_CREDENTIALS apontar para arquivo,
        # você usa a variável GOOGLE_CREDENTIALS_JSON (conteúdo da chave).
        env {
          name  = "GOOGLE_CREDENTIALS_JSON"
          value = var.google_credentials_json
        }
      }
    }
  }
}


