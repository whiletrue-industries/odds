# CKANGPT API

## Deploy

Make sure you are connected to the relevant cluster

```
export KUBECONFIG=/etc/ckangpt/.kubeconfig
kubectl get nodes
```

Deploy

```
helm upgrade --install api infra/apps/api --namespace api --create-namespace --values infra/apps/api/values.auto-updated.yaml
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

```
htpasswd -c auth <USERNAME>
kubectl -n api create secret generic basic-auth --from-file=auth
rm auth
```
