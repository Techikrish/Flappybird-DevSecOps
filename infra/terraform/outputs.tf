output "cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "EKS API server endpoint."
  value       = aws_eks_cluster.main.endpoint
}

output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block."
  value       = aws_vpc.main.cidr_block
}

output "rds_endpoint" {
  description = "PostgreSQL endpoint to plug into Helm."
  value       = aws_db_instance.flappy.endpoint
}

output "db_username" {
  description = "RDS master username."
  value       = aws_db_instance.flappy.username
  sensitive   = false
}
