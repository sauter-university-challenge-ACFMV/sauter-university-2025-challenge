locals {
  bucket_names = { for n in var.names : n => "${var.project_id}-${var.env}-${n}" }
}

resource "google_storage_bucket" "buckets" {
  for_each                      = local.bucket_names
  name                          = each.value            # nomes têm que ser globais únicos
  location                      = var.location
  uniform_bucket_level_access   = true                  # usa só IAM
  force_destroy                 = false

  versioning { enabled = true }                         # guarda versões

  labels = {
    env       = var.env
    data_zone = each.key
  }
}
