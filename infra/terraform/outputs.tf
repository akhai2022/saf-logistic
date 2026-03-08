# -----------------------------------------------------------------------------
# Outputs
# -----------------------------------------------------------------------------

# ── Networking ───────────────────────────────────────────────────────────────

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

# ── Load Balancer ────────────────────────────────────────────────────────────

output "alb_dns_name" {
  description = "ALB DNS name — entry point for the application"
  value       = aws_lb.main.dns_name
}

output "app_url" {
  description = "Application URL"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "http://${aws_lb.main.dns_name}"
}

# ── Database ─────────────────────────────────────────────────────────────────

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

# ── Redis ────────────────────────────────────────────────────────────────────

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
}

# ── S3 ───────────────────────────────────────────────────────────────────────

output "s3_bucket_name" {
  description = "S3 bucket for document storage"
  value       = aws_s3_bucket.docs.id
}

# ── ECR Repositories ────────────────────────────────────────────────────────

output "ecr_api_url" {
  description = "ECR repository URL for API image"
  value       = aws_ecr_repository.api.repository_url
}

output "ecr_worker_ocr_url" {
  description = "ECR repository URL for OCR worker image"
  value       = aws_ecr_repository.worker_ocr.repository_url
}

output "ecr_frontend_url" {
  description = "ECR repository URL for frontend image"
  value       = aws_ecr_repository.frontend.repository_url
}

# ── ECS ──────────────────────────────────────────────────────────────────────

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

# ── DNS ──────────────────────────────────────────────────────────────────────

output "route53_zone_id" {
  description = "Route53 hosted zone ID (set NS records at your registrar)"
  value       = var.domain_name != "" ? aws_route53_zone.main[0].zone_id : null
}

output "route53_name_servers" {
  description = "Route53 name servers — configure these at your domain registrar"
  value       = var.domain_name != "" ? aws_route53_zone.main[0].name_servers : []
}
