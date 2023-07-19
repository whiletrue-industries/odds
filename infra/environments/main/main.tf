terraform {
  cloud {
    organization = "ckangpt"
    workspaces {
      name = "main"
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3"
    }
  }
}

provider "azurerm" {
  tenant_id = local.tenant_id
  subscription_id = local.subscription_id
  features {}
}

resource "azurerm_resource_group" "ckangpt" {
  name = local.resource_group_name
  location = local.location
}
