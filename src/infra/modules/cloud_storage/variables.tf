variable "project_id" { type = string }
variable "location"   { type = string }   # ex.: southamerica-east1
variable "env"        { type = string }   # ex.: dev
variable "names" {
  type    = list(string)
  default = ["raw"]
}
