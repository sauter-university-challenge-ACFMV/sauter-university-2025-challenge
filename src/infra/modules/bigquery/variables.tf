variable "project_id" { type = string }
variable "location"   { type = string }   # ex.: southamerica-east1
variable "env"        { type = string }   # ex.: dev
variable "datasets" {
  type    = list(string)
  default = ["bronze", "silver", "gold","procedure"]
}
