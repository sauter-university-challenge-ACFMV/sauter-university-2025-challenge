output "dataset_ids" {
  value = [for k, v in google_bigquery_dataset.ds : v.dataset_id]
}
