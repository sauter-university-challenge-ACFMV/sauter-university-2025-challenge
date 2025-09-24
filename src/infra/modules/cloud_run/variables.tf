variable "project_id" { type = string }
variable "region"     { type = string }
variable "name"       { type = string }  # ex: "baseline-api"
variable "image"      { type = string }  # ex: "us-docker.pkg.dev/cloudrun/container/hello"
variable "env"        { type = string }
variable "service_account_email" { type = string }
variable "allow_unauthenticated" {
  type    = bool
  default = true
}
variable "secret_environment_variables" {
  description = "Um mapa de objetos para variáveis de ambiente montadas a partir do Secret Manager."
  type = map(object({
    secret_name    = string
    secret_version = string
  }))
  default = {}
}