# ArgoCD

## Deploy

Make sure you are connected to the relevant cluster

```
export KUBECONFIG=/etc/ckangpt/.kubeconfig
kubectl get nodes
```

Deploy

```
kubectl create ns argocd
kubectl apply -n argocd -k infra/apps/argocd
```