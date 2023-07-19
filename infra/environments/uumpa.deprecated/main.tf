terraform {
  backend "remote" {
    hostname = "app.terraform.io"
    organization = "uumpa"
    workspaces {
      name = "ckangpt"
    }
  }
  required_providers {
    contabo = {
      source = "contabo/contabo"
      version = ">= 0.1.17"
    }
  }
}

variable "contabo_oauth2_client_id" {}
variable "contabo_oauth2_client_secret" {}
variable "contabo_oauth2_user" {}
variable "contabo_oauth2_pass" {}

provider "contabo" {
  oauth2_client_id = var.contabo_oauth2_client_id
  oauth2_client_secret = var.contabo_oauth2_client_secret
  oauth2_user = var.contabo_oauth2_user
  oauth2_pass = var.contabo_oauth2_pass
}

variable "server_password" {}
