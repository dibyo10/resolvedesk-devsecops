# AWS infrastructure

Terraform provisions a VPC across two availability zones, two public and two private subnets, one NAT gateway, an EKS cluster, two managed worker nodes, and the EBS CSI driver with its own IAM service-account role. Workers use private subnets. Public API access is restricted to the CIDRs you supply; internal access remains enabled.

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

The cluster creator receives administrative access. Deploy using `../helm/resolvedesk/README.md`. Capture plan output and AWS VPC/EKS console evidence before cleanup. This classroom deployment uses one NAT gateway and a single PostgreSQL pod; it is not a production high-availability database.

Before destroying, uninstall application and monitoring Helm releases and ingress LoadBalancer services so their cloud resources can be removed. The gp3 StorageClass retains volumes deliberately; back up data and explicitly remove retained volumes when the exercise is finished. Then run:

```bash
terraform destroy
```

Capture destroy completion output. Keep state files private and preserve them until cleanup finishes. The provider lockfile is committed for reproducible provider selection; state, plans, local variables and credentials are excluded.
