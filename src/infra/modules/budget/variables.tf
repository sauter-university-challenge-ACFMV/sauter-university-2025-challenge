variable "billing_account" { type = string }   
variable "project_number"  { type = string }   # ex: 944848021706
variable "amount"          { type = number }   # valor do orçamento mensal

variable "currency_code" {
  type    = string
  default = "BRL"
}

variable "monitoring_channel_ids" {
  type    = list(string)
  default = []
}
