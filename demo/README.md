# ResolveDesk demonstration and evidence

This directory contains real browser captures, recorded command output, slides and an automated narrated walkthrough. Tickets use synthetic data. The narrator is a disclosed macOS synthetic voice; it does not imitate the student.

## Presentation

- [Walkthrough video](walkthrough.mp4): slides first, live application and code overview, an actual new push and complete CI run, AWS evidence, Kubernetes, Helm, ArgoCD, Prometheus, Grafana and troubleshooting.
- [PowerPoint](presentation.pptx) and [PDF slides](slides.pdf): ten slides.
- [Editable slide content](slides.json) and [presentation runbook](walkthrough.txt).

The recording preserves the live CI waiting period. Its final monitoring segment was recorded with a fresh login after Grafana restarted during setup; the obsolete login-screen segment was replaced with that genuine live capture. AWS Console images are identified as captured evidence in the narration.

## Verification by rubric module

| Module | Evidence |
|---|---|
| Application | [Desktop](evidence/application-desktop.png), [mobile](evidence/application-mobile.png), [creation](evidence/ticket-create.png), [browser checks](evidence/browser-check.json), [PostgreSQL records](evidence/postgresql-tickets.txt), [restart persistence](evidence/http-smoke.txt) |
| Testing | [26 passing backend tests](evidence/pytest.png), [raw output](evidence/pytest.txt); four frontend tests pass in CI |
| Git | [Commit history](evidence/git-history.png), [repository](https://github.com/dibyo10/resolvedesk-devsecops) |
| Docker | [Healthy Compose stack](evidence/compose-status.png), [build output](evidence/compose-build.log), [backend nonroot user](evidence/backend-user.txt), [frontend nonroot user](evidence/frontend-user.txt) |
| CI/CD | [Tested application run](https://github.com/dibyo10/resolvedesk-devsecops/actions/runs/38901458687), [new push recorded live](https://github.com/dibyo10/resolvedesk-devsecops/actions/runs/38902868534), [backend registry](evidence/resolvedesk-backend-ghcr.png), [frontend registry](evidence/resolvedesk-frontend-ghcr.png) |
| Security | [Backend Trivy report](evidence/trivy-backend.txt), [frontend Trivy report](evidence/trivy-frontend.txt) |
| Terraform | [Recovered plan](evidence/terraform-plan.log), [recovery apply log](evidence/terraform-apply.log), [VPC Console](evidence/aws-vpc-console.png), [EKS Console](evidence/aws-eks-console.png) |
| Kubernetes / Helm | [Pods](evidence/eks-pods.png), [Services](evidence/eks-services.png), [Helm](evidence/eks-helm.png), [HPA](evidence/eks-hpa.png), [persistent storage](evidence/eks-storage.png), [live ingress](evidence/eks-ingress-application.png), [ArgoCD](evidence/argocd-synced.png) |
| Observability | [Metrics](evidence/metrics.png), [Prometheus targets](evidence/prometheus-targets.png), [Grafana](evidence/grafana-dashboard.png), [live Prometheus data](evidence/eks-request-rate.json) |
| Troubleshooting | [Failure and repair screenshot](evidence/troubleshooting.png), [complete actual run](evidence/troubleshooting-live.txt) |

Command-output PNGs are readable renderings of the adjacent captured text, not terminal-emulator screenshots. Application, AWS, GitHub, ArgoCD, Prometheus and Grafana screenshots are actual browser captures.

## Results and limits

Both application images passed strict HIGH/CRITICAL Trivy scans, including unfixed findings. A clean scan reports the scanner's findings at that time; it does not prove the absence of all security flaws.

EKS ran two frontend and two backend replicas, with PostgreSQL on a persistent gp3 volume. ArgoCD reached Synced, Healthy and Succeeded. Prometheus showed both backend replicas UP, Grafana request-rate and latency panels contained actual traffic, and HPA had valid CPU measurements. The Grafana server-error panel has no matching series because no server-error series was observed; it is not presented as a measured zero.

The temporary cluster is shared with Aryan's CampusDesk project. Separate namespaces, Secrets and persistent volumes isolate the applications. The AWS screenshots and infrastructure logs describe that shared cluster. The initial NAT plan failed because the existing account had exhausted its Elastic IP quota; recovery used public-subnet workers with no public inbound node rules and an operator-IP-restricted Kubernetes API. Initial failure logs are retained alongside the recovery evidence. Both applications ran successfully on the recovered cluster, but the recovery apply was interrupted during AWS deletion of the obsolete failed worker group so teardown could proceed without retaining healthy workers. The apply log is not presented as a completed successful apply; the Kubernetes, browser and monitoring evidence establishes the actual deployed result.

Terraform destroy completed with 59 resources destroyed. The [destroy output](evidence/terraform-destroy.log), [completion screenshot](evidence/terraform-destroy-summary.png), [cleanup audit](evidence/aws-cleanup-audit.txt) and [machine-readable audit](evidence/aws-cleanup-audit.json) record the result. All 11 cleanup checks passed: the cluster and VPC are absent, all four owned EC2 instances are terminated, the application EBS volumes are deleted, no owned network resources remain, and Terraform state is empty. The owned KMS key is PendingDeletion until November 15, 2026, under AWS’s waiting period. Unrelated account resources were untouched. Local Docker applications remain available.

## Reproduce the artifacts

Install optional tools with `pip install -r scripts/requirements.txt` and `python -m playwright install chromium`. Run `python3 scripts/build-presentation.py` to rebuild the deck. `scripts/render-evidence.py` renders actual saved output. `scripts/record-walkthrough.py` requires macOS `say`, FFmpeg and ffprobe; its CI scene requires a real unpushed commit and follows the new run until completion. Browser authentication state remains outside the repository.

Run `python3 scripts/smoke-api.py --base-url http://localhost:8000` against the local application for the HTTP smoke checks. The demonstration has no authentication or HA database and is intended for synthetic classroom data only.
