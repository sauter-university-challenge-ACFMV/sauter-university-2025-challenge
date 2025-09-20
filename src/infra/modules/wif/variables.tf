variable "project_id" {
  type        = string
  description = "The GCP project ID where resources will be created."
}

variable "pool_id" {
  type        = string
  description = "The Workload Identity Pool ID. Example: \"github\""
}

variable "provider_id" {
  type        = string
  description = "The Workload Identity Provider ID. Example: \"github\""
}

variable "github_repo" {
  type        = string
  description = "The GitHub repository in the format \"owner/repo\"."
}

variable "sa_email" {
  type        = string
  description = "The email address of the Google Service Account to be used (e.g., terraform-deployer@...)."
}
