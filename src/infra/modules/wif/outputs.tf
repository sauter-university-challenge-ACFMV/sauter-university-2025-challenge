output "provider_resource_name" {
  value = google_iam_workload_identity_pool_provider.provider.name
}
output "pool_name" {
  value = google_iam_workload_identity_pool.pool.name
}
