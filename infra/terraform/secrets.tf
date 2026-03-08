# -----------------------------------------------------------------------------
# Secrets Manager — application secrets
# -----------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "app_secrets" {
  name                    = "${local.prefix}/app-secrets"
  description             = "SAF-Logistic application secrets"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = { Name = "${local.prefix}-app-secrets" }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id

  secret_string = jsonencode({
    APP_SECRET_KEY  = var.app_secret_key
    DB_PASSWORD     = var.db_password
    DATABASE_URL    = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}"
    REDIS_URL       = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
    S3_BUCKET       = aws_s3_bucket.docs.id
    S3_REGION       = var.aws_region
  })
}
