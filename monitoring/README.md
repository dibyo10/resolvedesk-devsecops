# Prometheus and Grafana

Install the Prometheus Operator and Grafana before enabling the application's ServiceMonitor:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack --version 92.9.0 \
  --namespace monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml -f monitoring/grafana-values.yaml \
  --wait --timeout 10m
kubectl create configmap resolvedesk-dashboard -n monitoring \
  --from-file=resolvedesk.json=monitoring/resolvedesk-dashboard.json \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl label configmap resolvedesk-dashboard -n monitoring grafana_dashboard=1 --overwrite
helm upgrade resolvedesk helm/resolvedesk -n resolvedesk --reuse-values \
  --set monitoring.serviceMonitor.enabled=true --wait --wait-for-jobs
```

Access the UIs without exposing them publicly:

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80
```

Run the port-forward commands in separate terminals. Read the generated Grafana administrator password from the `kube-prometheus-stack-grafana` Secret locally; never save it in evidence or Git. Open Prometheus at `http://localhost:9090/targets` and Grafana at `http://localhost:3001`, then open **ResolveDesk API**.

Generate traffic against `/api/tickets` repeatedly and allow two scrape intervals. The dashboard shows request rate, p95 latency, and server errors. A zero error rate is a valid result. Queries select `namespace="resolvedesk"`; update the selector when using another namespace. The dashboard expects the default kube-prometheus-stack datasource UID `prometheus`.

Capture `/metrics`, an UP Prometheus target, and a populated Grafana dashboard as separate evidence. A chart installation or dashboard JSON alone does not prove live scraping. Grafana storage is ephemeral for this classroom demo; the dashboard source stays in Git.
