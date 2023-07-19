# Main CKANGPT Infrastructure

## Prerequisites

* Terraform
* Login to Terraform Cloud with permissions to the relevant workspace
* Make sure the Terraform Cloud workspace is configured for Local execution mode
* Azure CLI Logged in with relevant permissions (`az login`)

## Deploy

```
terraform -chdir=infra/environments/main init
terraform -chdir=infra/environments/main apply
```

## K8S

Save the Kubeconfig

```
terraform -chdir=infra/environments/main output -raw kube_admin_config \
    > /etc/ckangpt/.kubeconfig
```