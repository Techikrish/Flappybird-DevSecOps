variable "project_name" {
  description = "Prefix for all AWS resources."
  type        = string
  default     = "flappybird"
}

variable "aws_region" {
  description = "AWS region for the deployment."
  type        = string
  default     = "us-east-1"
}

variable "cluster_version" {
  description = "Desired Kubernetes version for the EKS cluster."
  type        = string
  default     = "1.29"
}

variable "node_instance_types" {
  description = "Instance types for the EKS managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "desired_capacity" {
  description = "Desired worker count for the node group."
  type        = number
  default     = 2
}

variable "db_username" {
  description = "Master username for PostgreSQL."
  type        = string
  default     = "flappy"
}

variable "db_password" {
  description = "Master password for PostgreSQL."
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Instance size for RDS."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage (GB) for RDS."
  type        = number
  default     = 20
}

