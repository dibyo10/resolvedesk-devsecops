variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "cluster_name" {
  type    = string
  default = "resolvedesk-eks"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "kubernetes_version" {
  type    = string
  default = "1.35"
}

variable "cluster_public_access_cidrs" {
  type        = list(string)
  description = "Public CIDRs allowed to access the EKS API; use your current public IP with /32."
  validation {
    condition     = length(var.cluster_public_access_cidrs) > 0 && alltrue([for cidr in var.cluster_public_access_cidrs : can(cidrnetmask(cidr)) && cidr != "0.0.0.0/0"])
    error_message = "Supply explicit IPv4 CIDRs; unrestricted public API access is not allowed."
  }
}
