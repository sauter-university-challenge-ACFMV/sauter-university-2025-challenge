output "wif_provider" {
  value = module.wif.provider_resource_name
}

output "wif_pool" {
  value = module.wif.pool_name
}

output "terraform_sa" {
  value = module.iam.terraform_sa_email
}
