variable "project_id" { type = string }
variable "region"     { type = string }
variable "name"       { type = string }  # ex: "baseline-api"
variable "image"      { type = string }  # ex: "us-docker.pkg.dev/cloudrun/container/hello"
variable "service_account_email" { type = string }
variable "allow_unauthenticated" {
  type    = bool
  default = true
}
