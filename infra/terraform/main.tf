# ──────────────────────────────────────────────
# SAF-Logistic — Shared Infrastructure Deployment
# Attaches to the Formation ALB (dataforgeai.fr)
# Uses shared VPC, RDS, ECS cluster, Redis
# ──────────────────────────────────────────────

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge({
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }, var.tags)
  }
}

locals {
  prefix   = "${var.project_name}-${var.environment}"
  api_fqdn = "${var.api_subdomain}.${var.domain_name}"
  web_fqdn = "${var.web_subdomain}.${var.domain_name}"
}

# ──────────────────────────────────────────────
# Data Sources — Existing Infrastructure
# ──────────────────────────────────────────────
data "aws_vpc" "existing" {
  id = var.existing_vpc_id
}

data "aws_caller_identity" "current" {}

# Formation ALB (dataforgeai.fr)
data "aws_lb" "formation" {
  name = var.existing_alb_name
}

data "aws_lb_listener" "formation_https" {
  load_balancer_arn = data.aws_lb.formation.arn
  port              = 443
}

# Route53 zone for dataforgeai.fr (managed by Formation)
data "aws_route53_zone" "main" {
  name = var.domain_name
}

# ──────────────────────────────────────────────
# ECR Repositories
# ──────────────────────────────────────────────
resource "aws_ecr_repository" "api" {
  name                 = "${local.prefix}-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_repository" "web" {
  name                 = "${local.prefix}-web"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "web" {
  repository = aws_ecr_repository.web.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# ──────────────────────────────────────────────
# Security Groups
# ──────────────────────────────────────────────

# Backend (API + Worker) — accepts traffic from Formation ALB on port 8000
resource "aws_security_group" "ecs_backend" {
  name_prefix = "${local.prefix}-ecs-backend-"
  vpc_id      = data.aws_vpc.existing.id
  description = "SAF-Logistic ECS backend tasks (API + Worker)"

  ingress {
    description     = "From Formation ALB on API port"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [var.existing_alb_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Web — accepts traffic from Formation ALB on port 3000
resource "aws_security_group" "ecs_web" {
  name_prefix = "${local.prefix}-ecs-web-"
  vpc_id      = data.aws_vpc.existing.id
  description = "SAF-Logistic ECS web tasks"

  ingress {
    description     = "From Formation ALB on Web port"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [var.existing_alb_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle {
    create_before_destroy = true
  }
}

# CRITICAL: Allow SAF-Logistic backend tasks to reach the shared RDS
resource "aws_security_group_rule" "rds_from_saf_backend" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ecs_backend.id
  security_group_id        = var.existing_rds_security_group_id
  description              = "Allow SAF-Logistic backend (API + Worker) to reach shared RDS"
}

# ──────────────────────────────────────────────
# ACM Certificate for saf subdomains
# ──────────────────────────────────────────────
resource "aws_acm_certificate" "saf" {
  domain_name               = local.web_fqdn
  subject_alternative_names = [local.api_fqdn]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.saf.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.main.zone_id
}

resource "aws_acm_certificate_validation" "saf" {
  certificate_arn         = aws_acm_certificate.saf.arn
  validation_record_fqdns = [for record in aws_route53_record.acm_validation : record.fqdn]
}

# Attach SAF certificate to the Formation HTTPS listener
resource "aws_lb_listener_certificate" "saf" {
  listener_arn    = data.aws_lb_listener.formation_https.arn
  certificate_arn = aws_acm_certificate_validation.saf.certificate_arn
}

# ──────────────────────────────────────────────
# Target Groups
# ──────────────────────────────────────────────
resource "aws_lb_target_group" "api" {
  name        = "${local.prefix}-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.existing.id
  target_type = "ip"

  health_check {
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 15
    matcher             = "200"
  }

  deregistration_delay = 30

  stickiness {
    type    = "lb_cookie"
    enabled = false
  }
}

resource "aws_lb_target_group" "web" {
  name        = "${local.prefix}-web-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.existing.id
  target_type = "ip"

  health_check {
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 15
    matcher             = "200,307"
  }

  deregistration_delay = 30
}

# ──────────────────────────────────────────────
# Listener Rules (host-header routing on Formation ALB)
# ──────────────────────────────────────────────
resource "aws_lb_listener_rule" "api" {
  listener_arn = data.aws_lb_listener.formation_https.arn
  priority     = var.listener_rule_priority_api

  condition {
    host_header {
      values = [local.api_fqdn]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

resource "aws_lb_listener_rule" "web" {
  listener_arn = data.aws_lb_listener.formation_https.arn
  priority     = var.listener_rule_priority_web

  condition {
    host_header {
      values = [local.web_fqdn]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# ──────────────────────────────────────────────
# Route53 Records
# ──────────────────────────────────────────────
resource "aws_route53_record" "api" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.api_fqdn
  type    = "A"

  alias {
    name                   = data.aws_lb.formation.dns_name
    zone_id                = data.aws_lb.formation.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "web" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.web_fqdn
  type    = "A"

  alias {
    name                   = data.aws_lb.formation.dns_name
    zone_id                = data.aws_lb.formation.zone_id
    evaluate_target_health = true
  }
}

# ──────────────────────────────────────────────
# CloudWatch Log Groups
# ──────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.prefix}-api"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "web" {
  name              = "/ecs/${local.prefix}-web"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${local.prefix}-worker"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "migration" {
  name              = "/ecs/${local.prefix}-migration"
  retention_in_days = 14
}

# ──────────────────────────────────────────────
# IAM — ECS Execution Role
# ──────────────────────────────────────────────
resource "aws_iam_role" "ecs_execution" {
  name = "${local.prefix}-ecs-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_base" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_policy" "ecs_execution_secrets" {
  name = "${local.prefix}-ecs-exec-secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
      ]
      Resource = [
        "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${local.prefix}/*"
      ]
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_secrets" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = aws_iam_policy.ecs_execution_secrets.arn
}

# ──────────────────────────────────────────────
# IAM — ECS Task Role
# ──────────────────────────────────────────────
resource "aws_iam_role" "ecs_task" {
  name = "${local.prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "ecs_task" {
  name = "${local.prefix}-ecs-task-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssmmessages:CreateControlChannel",
          "ssmmessages:CreateDataChannel",
          "ssmmessages:OpenControlChannel",
          "ssmmessages:OpenDataChannel",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:HeadBucket",
        ]
        Resource = [
          aws_s3_bucket.docs.arn,
          "${aws_s3_bucket.docs.arn}/*",
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.ecs_task.arn
}

# ──────────────────────────────────────────────
# Secrets Manager
# ──────────────────────────────────────────────
resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${local.prefix}/database-url"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret" "app_secret_key" {
  name                    = "${local.prefix}/app-secret-key"
  recovery_window_in_days = 0
}

# ──────────────────────────────────────────────
# S3 Bucket (document storage)
# ──────────────────────────────────────────────
resource "aws_s3_bucket" "docs" {
  bucket        = "${local.prefix}-docs"
  force_destroy = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "docs" {
  bucket = aws_s3_bucket.docs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "docs" {
  bucket                  = aws_s3_bucket.docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ──────────────────────────────────────────────
# ECS Task Definition — API
# ──────────────────────────────────────────────
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "api"
    image     = "${aws_ecr_repository.api.repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]

    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "CORS_ORIGINS", value = "https://${local.web_fqdn}" },
      { name = "S3_BUCKET", value = aws_s3_bucket.docs.id },
      { name = "S3_REGION", value = var.aws_region },
      { name = "S3_USE_PATH_STYLE", value = "false" },
      { name = "S3_ENDPOINT_URL", value = "" },
      { name = "S3_ACCESS_KEY", value = "" },
      { name = "S3_SECRET_KEY", value = "" },
      { name = "CELERY_BROKER_URL", value = "${var.existing_redis_url}/${var.redis_db_broker}" },
      { name = "CELERY_RESULT_BACKEND", value = "${var.existing_redis_url}/${var.redis_db_result}" },
      { name = "OCR_PROVIDER", value = "MOCK" },
    ]

    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "APP_SECRET_KEY", valueFrom = aws_secretsmanager_secret.app_secret_key.arn },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval    = 15
      timeout     = 5
      retries     = 3
      startPeriod = 10
    }
  }])
}

# ──────────────────────────────────────────────
# ECS Task Definition — Web
# ──────────────────────────────────────────────
resource "aws_ecs_task_definition" "web" {
  family                   = "${local.prefix}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.web_cpu
  memory                   = var.web_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "web"
    image     = "${aws_ecr_repository.web.repository_url}:latest"
    essential = true

    portMappings = [{
      containerPort = 3000
      hostPort      = 3000
      protocol      = "tcp"
    }]

    environment = [
      { name = "NODE_ENV", value = "production" },
      { name = "NEXT_PUBLIC_API_URL", value = "https://${local.api_fqdn}" },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.web.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "web"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1"]
      interval    = 15
      timeout     = 5
      retries     = 3
      startPeriod = 10
    }
  }])
}

# ──────────────────────────────────────────────
# ECS Task Definition — Worker (Celery + Beat)
# ──────────────────────────────────────────────
resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "worker"
    image     = "${aws_ecr_repository.api.repository_url}:latest"
    essential = true

    command = [
      "celery", "-A", "app.infra.tasks_register",
      "worker", "-l", "INFO", "-Q", "default", "--beat",
    ]

    environment = [
      { name = "ENVIRONMENT", value = var.environment },
      { name = "S3_BUCKET", value = aws_s3_bucket.docs.id },
      { name = "S3_REGION", value = var.aws_region },
      { name = "S3_USE_PATH_STYLE", value = "false" },
      { name = "S3_ENDPOINT_URL", value = "" },
      { name = "S3_ACCESS_KEY", value = "" },
      { name = "S3_SECRET_KEY", value = "" },
      { name = "CELERY_BROKER_URL", value = "${var.existing_redis_url}/${var.redis_db_broker}" },
      { name = "CELERY_RESULT_BACKEND", value = "${var.existing_redis_url}/${var.redis_db_result}" },
      { name = "OCR_PROVIDER", value = "MOCK" },
    ]

    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
      { name = "APP_SECRET_KEY", valueFrom = aws_secretsmanager_secret.app_secret_key.arn },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker"
      }
    }
  }])
}

# ──────────────────────────────────────────────
# ECS Task Definition — Migration (one-off)
# ──────────────────────────────────────────────
resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.prefix}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "migration"
    image     = "${aws_ecr_repository.api.repository_url}:latest"
    essential = true

    command = ["alembic", "upgrade", "head"]

    environment = [
      { name = "ENVIRONMENT", value = var.environment },
    ]

    secrets = [
      { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.migration.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "migrate"
      }
    }
  }])
}

# ──────────────────────────────────────────────
# ECS Services
# ──────────────────────────────────────────────
resource "aws_ecs_service" "api" {
  name            = "${local.prefix}-api"
  cluster         = var.existing_ecs_cluster_arn
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  health_check_grace_period_seconds  = 30

  network_configuration {
    subnets          = var.existing_private_subnet_ids
    security_groups  = [aws_security_group.ecs_backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  enable_execute_command = true

  lifecycle {
    ignore_changes = [desired_count, task_definition]
  }

  depends_on = [aws_lb_listener_rule.api]
}

resource "aws_ecs_service" "web" {
  name            = "${local.prefix}-web"
  cluster         = var.existing_ecs_cluster_arn
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_maximum_percent         = 200
  deployment_minimum_healthy_percent = 100
  health_check_grace_period_seconds  = 30

  network_configuration {
    subnets          = var.existing_private_subnet_ids
    security_groups  = [aws_security_group.ecs_web.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn
    container_name   = "web"
    container_port   = 3000
  }

  enable_execute_command = true

  lifecycle {
    ignore_changes = [desired_count, task_definition]
  }

  depends_on = [aws_lb_listener_rule.web]
}

resource "aws_ecs_service" "worker" {
  name            = "${local.prefix}-worker"
  cluster         = var.existing_ecs_cluster_arn
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = var.existing_private_subnet_ids
    security_groups  = [aws_security_group.ecs_backend.id]
    assign_public_ip = false
  }

  enable_execute_command = true

  lifecycle {
    ignore_changes = [desired_count, task_definition]
  }
}
