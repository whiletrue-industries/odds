# Ingress

## Deploy

Make sure you are connected to the relevant cluster

```
export KUBECONFIG=/etc/ckangpt/.kubeconfig
kubectl get nodes
```

Deploy

```
helm upgrade --install ingress infra/apps/ingress --namespace ingress --create-namespace
```

Create secrets

```
kubectl create secret generic --namespace api openai-api-key \
    --from-literal=OPENAI_API_KEY=<api_key>
```

```
kubectl create secret docker-registry ghcr-pull-secret \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=<github-personal-access-token> \
  --namespace=api
```