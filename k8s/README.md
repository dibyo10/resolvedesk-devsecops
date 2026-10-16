# Cluster bootstrap

The application resources are managed by `helm/resolvedesk`; standalone duplicate Deployments are deliberately excluded. Namespace and bootstrap files here install prerequisites.

For the classroom demo, controller services use ClusterIP and are accessed through authenticated `kubectl port-forward`. ArgoCD runs HTTP behind that local tunnel and is not exposed publicly. Use TLS and an appropriate exposure policy before public access.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/storage-class.yaml
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --version 4.15.1 \
  -n ingress-nginx --create-namespace -f k8s/ingress-values.yaml --wait
helm upgrade --install metrics-server metrics-server/metrics-server --version 3.14.0 \
  -n kube-system --wait
helm upgrade --install argocd argo/argo-cd --version 10.10.5 \
  -n argocd --create-namespace -f k8s/argocd-values.yaml --wait
```

Use `storage-class.yaml` only on EKS with the EBS CSI addon. Kind uses its own default storage class.

For local ingress evidence:

```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8088:80
curl -H 'Host: resolvedesk.local' http://127.0.0.1:8088/api/tickets
```

Map `resolvedesk.local` to `127.0.0.1` locally and open `http://resolvedesk.local:8088` for browser evidence. This is a real Ingress route via the controller, accessed through a local tunnel.

For ArgoCD, follow the chart README to set published SHA tags, provision the database Secret, and apply `argocd-application.yaml`. Open the UI through:

```bash
kubectl port-forward -n argocd svc/argocd-server 8089:80
```

Read the initial admin password from the `argocd-initial-admin-secret` Secret locally; do not save it in logs or screenshots. Capture application Sync and Health status after reconciliation.
