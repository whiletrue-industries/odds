# Ingress

## Deploy

Make sure you are connected to the relevant cluster

```
export KUBECONFIG=/etc/ckangpt/.kubeconfig
kubectl get nodes
```

On first deployment, set in values.yaml issuer.enabled = false, then once it's deployed, set it to true

Deploy

```
helm dependency update infra/apps/ingress
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