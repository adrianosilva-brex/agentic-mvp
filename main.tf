variable "access_key" {
    type = string
}
variable "secret_key" {
    type = string
}
variable "region" {
    type = string
}
variable "localstack_endpoint" {
    type = string
}
variable "s3_bucket" {
    type = string
}

provider "aws" {

  access_key                  = var.access_key
  secret_key                  = var.secret_key
  region                      = var.region

  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    s3             = var.localstack_endpoint
  }
}

resource "aws_s3_bucket" "test-bucket" {
  bucket = var.s3_bucket
}