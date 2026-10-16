# ResolveDesk deployment

Requirements: Kubernetes, Helm, a default dynamic StorageClass (Kind) or `gp3` (EKS), and published backend/frontend image tags. Install an ingress controller before enabling ingress, Metrics Server before enabling HPA, and kube-prometheus-stack before enabling ServiceMonitor.

Create a namespace and an external Secret. The database password must be URL-encoded in `DATABASE_URL` if it contains special characters. For a generated hexadecimal password, the following command avoids that issue:

```bash
kubectl apply -f k8s/namespace.yaml
DB_PASSWORD=$(openssl rand -hex 24)
kubectl create secret generic resolvedesk-database -n resolvedesk \
  --from-literal=username=resolvedesk \
  --from-literal=password="$DB_PASSWORD" \
  --from-literal=DATABASE_URL="postgresql+psycopg://resolvedesk:$DB_PASSWORD@resolvedesk-postgres:5432/resolvedesk"
unset DB_PASSWORD
```

Do not regenerate the password for an existing PostgreSQL volume. Keep the Secret outside Git. GHCR images must be public or an existing registry pull Secret must be listed under `imagePullSecrets`.

```bash
helm lint helm/resolvedesk
helm upgrade --install resolvedesk helm/resolvedesk -n resolvedesk \
  -f helm/resolvedesk/values-dev.yaml \
  --set backend.tag="$IMAGE_SHA" --set frontend.tag="$IMAGE_SHA" \
  --wait --wait-for-jobs --timeout 10m
kubectl get pods,svc,ingress,hpa -n resolvedesk
helm list -n resolvedesk
```

Use the release name `resolvedesk`: the frontend Nginx upstream is `resolvedesk-backend`. Both application Deployments run two replicas. Backend liveness uses `/health`; readiness uses `/ready`. Frontend listens on 8080 behind Service port 80. Ingress preserves `/api` when routing to backend port 8000 and sends `/` to the frontend.

A single migration Job runs `alembic upgrade head` for each backend image. Backend init containers wait until the database revision matches the image's Alembic head before starting Uvicorn. Helm waits for completion with `--wait-for-jobs`; ArgoCD runs the same Job during Sync. Apply only one release against a given database at a time. Migrations must remain backward compatible during rolling upgrades. Old migration Jobs remain for inspection and may be pruned after release verification.

For EKS, apply `k8s/storage-class.yaml`, install monitoring first, and use `values-prod.yaml` with your own ingress hostname and TLS settings. `values-prod.yaml` enables ServiceMonitor and gp3 persistence. HPA requires Metrics Server. For a local cluster without Metrics Server, `values-dev.yaml` disables HPA.

## GitOps

Install ArgoCD using its official installation guide, then update `values-release.yaml` to the successfully published Git SHA for both images and push it. The example Application tracks the student's repository and uses production values with the local demonstration hostname `resolvedesk.local`. Install the EKS StorageClass, ingress controller, Metrics Server and monitoring before synchronization.

```bash
kubectl apply -f k8s/argocd-application.yaml
kubectl get application resolvedesk -n argocd
```

The external database Secret must already exist before synchronization. ArgoCD does not receive or generate database credentials. Demonstrate GitOps by changing the image tags in Git and observing the application become Synced and Healthy. `local` is only a development tag and must be replaced before using GHCR deployment.
