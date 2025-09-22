resource "google_logging_metric" "api_server_errors" {
    name        = "api-server-errors"
    project     = var.project_id
    description = "Contador de erros 500 Internal Server Error da API Cloud Run."
    filter      = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND severity=\"ERROR\" AND textPayload:\"500 Internal Server Error\""
}

resource "google_logging_project_sink" "api_logs_sink" {
	name        = "api-logs-sink"
	project     = var.project_id
	destination = "storage.googleapis.com/${var.bucket_name}"
	filter      = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\""
}

resource "google_storage_bucket_iam_member" "sink_writer" {
  bucket = var.bucket_name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.api_logs_sink.writer_identity
}
