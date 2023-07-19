output "kube_admin_config" {
  sensitive = true
  value = azurerm_kubernetes_cluster.main.kube_config_raw
}
