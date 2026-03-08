# -----------------------------------------------------------------------------
# ElastiCache Redis 7
# -----------------------------------------------------------------------------

resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.prefix}-redis-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${local.prefix}-redis-subnet" }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${local.prefix}-redis"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  num_cache_nodes      = 1
  port                 = 6379
  parameter_group_name = "default.redis7"

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  tags = { Name = "${local.prefix}-redis" }
}
