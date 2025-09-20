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
