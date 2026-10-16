# AWS infrastructure

Terraform provisions a VPC across two availability zones, two public and two private subnets, an EKS cluster, two managed worker nodes, and the EBS CSI driver with its own IAM service-account role. For this temporary classroom deployment, workers use public subnets with automatically assigned public IPs and no NAT gateway. Node security groups allow no unsolicited public inbound access. The EKS control plane uses private subnets. Public API access is restricted to the CIDRs you supply; internal access remains enabled.

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check
terraform validate
terraform plan -out=resolvedesk.tfplan
terraform apply resolvedesk.tfplan
```

Replace the example documentation IP in `terraform.tfvars` with your current public IPv4 `/32` before planning. Use an authenticated AWS profile; credentials never belong in `.tf` or `.tfvars`. Kubernetes 1.35 is selected from [AWS's supported versions](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html); check regional availability before applying.

```bash
aws eks update-kubeconfig --region ap-south-1 --name resolvedesk-eks
kubectl apply -f ../k8s/storage-class.yaml
```

The cluster creator receives administrative access. Deploy using `../helm/resolvedesk/README.md`. Capture plan output and AWS VPC/EKS console evidence before cleanup. The AWS account had no free Elastic IP quota, so NAT creation failed in the initial attempt. Public-subnet workers avoid changing unrelated infrastructure or raising quotas and reduce this temporary deployment cost. A production deployment should use private workers with a provisioned NAT gateway or required VPC endpoints. Each application uses a single PostgreSQL pod; this is not a production high-availability database.

Before destroying, uninstall application and monitoring Helm releases and ingress LoadBalancer services so their cloud resources can be removed. The gp3 StorageClass retains volumes deliberately; back up data and explicitly remove retained volumes when the exercise is finished. Then run:

```bash
terraform destroy
```

Capture destroy completion output. Keep state files private and preserve them until cleanup finishes. The provider lockfile is committed for reproducible provider selection; state, plans, local variables and credentials are excluded.

AWS browser-login credentials expire quickly. Use an AWS SDK credential_process profile that invokes `aws configure export-credentials --profile resolvedesk-capstone --format process`, so Terraform refreshes credentials during long operations. Never paste exported credential values into commands or commit them.

## Refreshable AWS browser-login credentials

AWS CLI browser login and the AWS 5.x Terraform provider use different credential-loading paths. A one-time export may expire during EKS creation. Keep two distinct profiles so the provider can refresh credentials without a recursive credential process:

```bash
aws login --profile resolvedesk-capstone --region ap-south-1
aws configure set region ap-south-1 --profile resolvedesk-terraform
aws configure set credential_process 'aws configure export-credentials --profile resolvedesk-capstone --format process' --profile resolvedesk-terraform
export AWS_PROFILE=resolvedesk-terraform
terraform init
terraform plan -out=resolvedesk.tfplan
terraform apply resolvedesk.tfplan
```

Use an AWS CLI version that supports `aws login`. The source profile is always `resolvedesk-capstone`; the consuming Terraform profile is always `resolvedesk-terraform`. Do not configure the process on the source profile itself. Clear old `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` environment variables before using the profile, since those variables take precedence. Profile configuration contains the command, not credential values. The CLI returns refreshed short-lived credentials directly to the provider.

For `kubectl`, `aws eks update-kubeconfig` and AWS CLI commands, continue using `--profile resolvedesk-capstone` or its `AWS_PROFILE` environment setting. The credential source must remain logged in until cleanup completes.
