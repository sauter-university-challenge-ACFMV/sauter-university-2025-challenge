variable "env" {
  type    = string
  default = "dev"
}
variable "project_id" {
  type = string
}

variable "region" {
  type    = string
  default = "southamerica-east1"
}

variable "bq_location" {
  type    = string
  default = "southamerica-east1"
}

variable "github_repo" {
  type = string
}

variable "dev_budget_amount" {
  type = number
}

variable "alert_group_email" {
  type = string
}
