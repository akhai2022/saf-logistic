# ──────────────────────────────────────────────
# Outputs
# ──────────────────────────────────────────────

output "web_url" {
  description = "Web frontend URL"
  value       = "https://${local.web_fqdn}"
}

output "api_url" {
  description = "API URL"
  value       = "https://${local.api_fqdn}"
}

output "ecr_api_url" {
  description = "ECR repository URL for the API image"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_web_url" {
  description = "ECR repository URL for the Web image"
  value       = aws_ecr_repository.web.repository_url
}

output "s3_bucket_name" {
  description = "S3 bucket name for document storage"
  value       = aws_s3_bucket.docs.id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = split("/", var.existing_ecs_cluster_arn)[1]
}

output "api_service_name" {
  description = "ECS API service name"
  value       = aws_ecs_service.api.name
}

output "web_service_name" {
  description = "ECS Web service name"
  value       = aws_ecs_service.web.name
}

output "worker_service_name" {
  description = "ECS Worker service name"
  value       = aws_ecs_service.worker.name
}

output "migration_task_definition" {
  description = "Migration task definition ARN"
  value       = aws_ecs_task_definition.migration.arn
}

output "backend_security_group_id" {
  description = "Security group ID for backend ECS tasks"
  value       = aws_security_group.ecs_backend.id
}
