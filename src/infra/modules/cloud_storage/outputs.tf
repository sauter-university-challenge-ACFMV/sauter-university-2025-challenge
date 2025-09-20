output "names" {
  value = [for k, v in google_storage_bucket.buckets : v.name]
}
