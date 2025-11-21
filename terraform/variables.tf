variable "region" {
  default = "ap-south-1"
}

variable "db_user" {
  type = string
}

variable "db_pass" {
  type = string
}

variable "cluster_role_arn" {
  description = "IAM role ARN for EKS cluster"
  type        = string
}

variable "worker_role_arn" {
  description = "Worker nodes IAM role ARN"
  type        = string
}
