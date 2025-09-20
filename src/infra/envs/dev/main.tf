locals {
  services = [
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "iamcredentials.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "billingbudgets.googleapis.com",
    "secretmanager.googleapis.com"
  ]
}

# Check if project is correct
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
