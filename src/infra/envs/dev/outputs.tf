output "wif_provider" {
  value = module.wif.provider_resource_name
}

output "wif_pool" {
  value = module.wif.pool_name
}

output "terraform_sa" {
  value = module.iam.terraform_sa_email
}

output "cloud_run_url" {
  value = module.cloud_run.url
}

output "buckets" {
  value = module.cloud_storage.names
}

output "dataset_ids" {
  value = module.bigquery.dataset_ids
}
