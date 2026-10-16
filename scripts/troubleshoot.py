import argparse
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMESPACE = "troubleshooting-lab"


def kubectl(*args):
    command = ["kubectl", *args]
    print("$ " + " ".join(command), flush=True)
    result = subprocess.run(command, text=True, capture_output=True)
    print(result.stdout, end="", flush=True)
    if result.stderr:
        print(result.stderr, end="", flush=True)
    result.check_returncode()
    return result.stdout


def wait_for(check, description, timeout=180):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            print(description, flush=True)
            return
        time.sleep(5)
    raise TimeoutError(description)


def image_failed():
    pods = json.loads(kubectl("get", "pods", "-n", NAMESPACE, "-o", "json"))
    return any(
        status.get("state", {}).get("waiting", {}).get("reason")
        in {"ErrImagePull", "ImagePullBackOff"}
        for pod in pods["items"]
        for status in pod.get("status", {}).get("containerStatuses", [])
    )


def endpoint_addresses():
    result = json.loads(kubectl("get", "endpointslice", "-n", NAMESPACE,
                               "-l", "kubernetes.io/service-name=broken-service", "-o", "json"))
    return [address for item in result["items"] for endpoint in (item.get("endpoints") or [])
            if endpoint.get("conditions", {}).get("ready") for address in endpoint.get("addresses", [])]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    args = parser.parse_args()
    namespaces = json.loads(kubectl("get", "namespace", "-o", "json"))
    if any(item["metadata"]["name"] == NAMESPACE for item in namespaces["items"]):
        raise RuntimeError("Refusing to modify an existing troubleshooting-lab namespace")
    kubectl("create", "namespace", NAMESPACE)
    try:
        kubectl("apply", "-f", str(ROOT / "troubleshooting/broken-image.yaml"))
        wait_for(image_failed, "Observed image pull failure for a nonexistent tag")
        kubectl("describe", "pods", "-n", NAMESPACE)
        kubectl("set", "image", "deployment/broken-image", "backend=" + args.image, "-n", NAMESPACE)
        kubectl("rollout", "status", "deployment/broken-image", "-n", NAMESPACE, "--timeout=180s")
        kubectl("apply", "-f", str(ROOT / "troubleshooting/broken-service.yaml"))
        assert not endpoint_addresses(), "Broken selector unexpectedly matched a pod"
        print("Observed zero ready endpoints for the incorrect selector", flush=True)
        kubectl("patch", "service", "broken-service", "-n", NAMESPACE,
                "--type=merge", "-p", json.dumps({"spec": {"selector": {"app": "broken-image"}}}))
        wait_for(endpoint_addresses, "Corrected selector has ready service endpoints")
        kubectl("exec", "-n", NAMESPACE, "deployment/broken-image", "--", "python", "-c",
                "import urllib.request; print(urllib.request.urlopen('http://broken-service:8080/health').read().decode())")
        kubectl("get", "pods,services,endpointslices", "-n", NAMESPACE)
        print("Both failures repaired successfully", flush=True)
    finally:
        try:
            kubectl("get", "pods,services,endpointslices", "-n", NAMESPACE)
        finally:
            kubectl("delete", "namespace", NAMESPACE, "--wait=false")
            print("Isolated lab namespace deletion requested", flush=True)


if __name__ == "__main__":
    main()
