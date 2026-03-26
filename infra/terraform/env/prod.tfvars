# ──────────────────────────────────────────────
# SAF-Logistic — Staging on Shared Infrastructure
# ──────────────────────────────────────────────

project_name = "saf-logistic"
environment  = "prod"
aws_region   = "us-east-1"

# ── Existing Infrastructure (shared with zinovia-fans + formation) ──
existing_vpc_id                = "vpc-04096ae7aea767aa8"
existing_private_subnet_ids    = ["subnet-0a9e6fae7d748035c", "subnet-042c9a22dba8de4df", "subnet-0258626a5bc51d490"]
existing_public_subnet_ids     = ["subnet-05958df9bb663b259", "subnet-0e84157288b0410a7", "subnet-08b23492b33c92edd"]
existing_rds_endpoint          = "zinovia-fans-prod-postgres.c8bweyw20bog.us-east-1.rds.amazonaws.com:5432"
existing_rds_security_group_id = "sg-0af2b56a2eed179bb"
existing_ecs_cluster_arn       = "arn:aws:ecs:us-east-1:208030346312:cluster/zinovia-fans-prod-cluster"

# ── Formation ALB (dataforgeai.fr) ──
existing_alb_name              = "zinovia-formation-prod-alb"
existing_alb_security_group_id = "sg-01c313d439bc1ca11"

# ── Redis (shared ElastiCache) ──
existing_redis_url = "redis://zinovia-fans-prod-redis.mlwucg.ng.0001.use1.cache.amazonaws.com:6379"
redis_db_broker    = 3
redis_db_result    = 4

# ── Domain (subdomains of dataforgeai.fr) ──
domain_name   = "dataforgeai.fr"
web_subdomain = "saf"
api_subdomain = "api-saf"

# ── Listener rule priorities (must not conflict with Formation: 10, 20) ──
listener_rule_priority_api = 30
listener_rule_priority_web = 35

# ── ECS sizing (staging — minimal) ──
api_cpu            = 512
api_memory         = 1024
api_desired_count  = 1

web_cpu            = 256
web_memory         = 512
web_desired_count  = 1

worker_cpu            = 512
worker_memory         = 1024
worker_desired_count  = 1

# ── Tags ──
tags = {
  Owner   = "akhai"
  Project = "saf-logistic"
}
