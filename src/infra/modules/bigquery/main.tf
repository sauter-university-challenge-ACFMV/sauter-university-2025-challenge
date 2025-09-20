resource "google_bigquery_dataset" "ds" {
  for_each   = toset(var.datasets)
  project    = var.project_id
  dataset_id = each.value
  location   = var.location

  labels = {
    env   = var.env
    tier  = each.value
  }

  # ajustes comuns (opcionais):
  # default_table_expiration_ms = 0
  # delete_contents_on_destroy  = false
}
