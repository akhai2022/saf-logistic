# -----------------------------------------------------------------------------
# ECS Cluster, Task Definitions & Services
# -----------------------------------------------------------------------------

resource "aws_ecs_cluster" "main" {
  name = "${local.prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = "${local.prefix}-cluster" }
}

# ── Common environment block (used by API + workers) ─────────────────────────

locals {
  redis_address = aws_elasticache_cluster.redis.cache_nodes[0].address
  redis_port    = aws_elasticache_cluster.redis.cache_nodes[0].port

  backend_env = [
    { name = "DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}" },
    { name = "CELERY_BROKER_URL", value = "redis://${local.redis_address}:${local.redis_port}/1" },
    { name = "CELERY_RESULT_BACKEND", value = "redis://${local.redis_address}:${local.redis_port}/2" },
    { name = "S3_BUCKET", value = aws_s3_bucket.docs.id },
    { name = "S3_REGION", value = var.aws_region },
    { name = "S3_USE_PATH_STYLE", value = "false" },
    { name = "APP_SECRET_KEY", value = var.app_secret_key },
  ]
}

# =============================================================================
# API Service
# =============================================================================

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
      protocol      = "tcp"
    }]

    environment = local.backend_env

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.api.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "api"
      }
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "${local.prefix}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
}

# =============================================================================
# Worker-Default Service
# =============================================================================

resource "aws_ecs_task_definition" "worker_default" {
  family                   = "${local.prefix}-worker-default"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_default_cpu
  memory                   = var.worker_default_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "worker-default"
    image     = "${aws_ecr_repository.api.repository_url}:latest"
    essential = true
    command   = ["celery", "-A", "app.infra.tasks_register", "worker", "-l", "INFO", "-Q", "default"]

    environment = local.backend_env

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker_default.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker-default"
      }
    }
  }])
}

resource "aws_ecs_service" "worker_default" {
  name            = "${local.prefix}-worker-default"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker_default.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
}

# =============================================================================
# Worker-OCR Service
# =============================================================================

resource "aws_ecs_task_definition" "worker_ocr" {
  family                   = "${local.prefix}-worker-ocr"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.worker_ocr_cpu
  memory                   = var.worker_ocr_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "worker-ocr"
    image     = "${aws_ecr_repository.worker_ocr.repository_url}:latest"
    essential = true

    environment = concat(local.backend_env, [
      { name = "OCR_PROVIDER", value = "OPEN_SOURCE" },
    ])

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.worker_ocr.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker-ocr"
      }
    }
  }])
}

resource "aws_ecs_service" "worker_ocr" {
  name            = "${local.prefix}-worker-ocr"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker_ocr.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }
}

# =============================================================================
# Frontend Service
# =============================================================================

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${local.prefix}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.frontend_cpu
  memory                   = var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name      = "frontend"
    image     = "${aws_ecr_repository.frontend.repository_url}:latest"
    essential = true
    command   = ["npm", "run", "start"]

    portMappings = [{
      containerPort = 3000
      protocol      = "tcp"
    }]

    environment = [
      { name = "NEXT_PUBLIC_API_URL", value = "http://${aws_lb.main.dns_name}" },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "frontend"
      }
    }
  }])
}

resource "aws_ecs_service" "frontend" {
  name            = "${local.prefix}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = var.frontend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.http]
}
