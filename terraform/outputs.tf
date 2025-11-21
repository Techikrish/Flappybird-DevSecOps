output "cluster_name" {
  value = aws_eks_cluster.cluster.name
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}
