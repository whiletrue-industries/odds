# CKANGPT API

## Deploy

Deployment is handled via ArgoCD

## Secrets

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
