# Mêmes sens que dans 01-bis-cloud-run-a2a/terraform/variables.tf.
variable "agents_project_id" { type = string }
variable "ge_project_number" {
  type    = string
  default = ""
}
variable "ge_project_id" {
  type    = string
  default = ""
}
variable "ge_app_id" {
  type    = string
  default = ""
}
variable "ge_location" {
  type    = string
  default = "eu"
}
variable "region" {
  type    = string
  default = "europe-west1"
}
variable "agents" {
  type    = list(string)
  default = []
}
