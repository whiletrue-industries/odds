# ckangpt

## Deploy

Deploy

```
export KUBECONFIG=/etc/ckangpt/uumpa-kubeconfig
helm upgrade --install ckangpt infra/apps/ckangpt --namespace ckangpt --create-namespace
```

Create secret `chroma-auth`

```
htpasswd -c auth <USERNAME>
kubectl -n ckangpt create secret generic basic-auth --from-file=auth
rm auth
```
