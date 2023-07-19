resource "azurerm_kubernetes_cluster" "main" {
  name                = "main"
  location            = local.location
  resource_group_name = azurerm_resource_group.ckangpt.name
  dns_prefix          = local.prefix
  sku_tier = "Free"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_DS2_v2"
  }

  identity {
    type = "SystemAssigned"
  }
}
