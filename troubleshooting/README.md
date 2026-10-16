# Failure investigation

These manifests create separate demonstration resources in the `resolvedesk` namespace. They do not alter the application Deployments or Services.

## Unavailable image

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n resolvedesk
kubectl describe deployment resolvedesk-broken-image -n resolvedesk
kubectl get events -n resolvedesk --sort-by=.lastTimestamp
kubectl delete -f troubleshooting/broken-image.yaml
```

The intentionally nonexistent image produces `ErrImagePull` and eventually `ImagePullBackOff`. Compare the image repository and tag with the successfully deployed backend before deleting the exercise resource.

## Service with no endpoints

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get pods -n resolvedesk --show-labels
kubectl get endpointslices -n resolvedesk -l kubernetes.io/service-name=broken-service
kubectl describe service broken-service -n resolvedesk
kubectl delete -f troubleshooting/broken-service.yaml
```

The selector matches no application pods. Compare it with the release and component labels on `resolvedesk-backend`. A Service port cannot route traffic when its selector has no matching ready pods. The working chart's backend Service targets the named `http` port at 8000.
