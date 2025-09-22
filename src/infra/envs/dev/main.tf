resource "google_storage_bucket" "logs" {
  name     = "sauter-university-challenger-dev-logs"
  location = var.region
  project  = var.project_id
  force_destroy = true 
}

module "logging" {
  source       = "../../modules/logging"
  project_id   = var.project_id
  service_name = module.cloud_run.service_name
  bucket_name  = google_storage_bucket.logs.name
}
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
  env        = var.env
}

module "cloud_run" {
  source                = "../../modules/cloud_run"
  project_id            = var.project_id
  region                = var.region
  name                  = "baseline-api"
  image                 = "us-docker.pkg.dev/cloudrun/container/hello"
  service_account_email = module.iam.runtime_sa_email
  allow_unauthenticated = true
  env                   = var.env
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
  service_name = module.cloud_run.service_name
}

module "budget" {
  source                 = "../../modules/budget"
  billing_account        = "012AA0-0BFB09-AC0D0F"
  project_number         = data.google_project.this.number
  amount                 = var.dev_budget_amount
  currency_code          = "BRL"
  monitoring_channel_ids = [module.monitoring.channel_id]
}

