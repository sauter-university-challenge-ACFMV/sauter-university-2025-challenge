output "terraform_sa_email" {
  value = google_service_account.terraform.email
}

output "runtime_sa_email" {
  value = google_service_account.runtime.email
}
