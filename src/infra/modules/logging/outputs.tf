output "logs_bucket_name" {
	value       = var.bucket_name
	description = "Nome do bucket onde os logs são exportados."
}

output "sink_name" {
	value       = google_logging_project_sink.api_logs_sink.name
	description = "Nome do Log Sink criado."
}

output "sink_writer_identity" {
	value       = google_logging_project_sink.api_logs_sink.writer_identity
	description = "Service Account usada pelo Log Sink para gravar no bucket."
}
