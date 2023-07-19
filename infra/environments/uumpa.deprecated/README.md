# ckangpt uumpa environment

## Deployment

Following are the full deployment steps, depending on what you want to do you can skip to relevant part

### Update the infrastructure

Set secret env vars:

```
TF_VAR_contabo_oauth2_client_id=
TF_VAR_contabo_oauth2_client_secret=
TF_VAR_contabo_oauth2_user=
TF_VAR_contabo_oauth2_pass=
TF_VAR_server_password= 
```

Apply:

```
terraform -chdir=infra/environments/uumpa init
terraform -chdir=infra/environments/uumpa apply
```

### Set SSH config to access the server

Add your ssh key in the terraform server.tf ssh_keys

Run terraform apply as described above, or the server admin to do it.

Set sshconfig to name the server `ckangpt`:

```
echo "
Host ckangpt
  HostName 173.212.219.159
  User admin
" >> ~/.ssh/config
```

### Access K8S

Save the kubeconfig from the server

```
sudo mkdir -p /etc/ckangpt
sudo chown -R $USER /etc/ckangpt
ssh ckangpt sudo k0s kubeconfig admin > /etc/ckangpt/uumpa-kubeconfig
```

Run kubectl commands

```
export KUBECONFIG=/etc/ckangpt/uumpa-kubeconfig
kubectl get nodes
```

### Deploy Ingress

```
export KUBECONFIG=/etc/ckangpt/uumpa-kubeconfig
helm upgrade --install ingress infra/environments/uumpa/ingress --namespace ingress --create-namespace
```
