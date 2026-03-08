# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

# ── ALB ──────────────────────────────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name_prefix = "${local.prefix}-alb-"
  description = "ALB - allow inbound HTTP/HTTPS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle { create_before_destroy = true }

  tags = { Name = "${local.prefix}-alb-sg" }
}

# ── ECS Tasks ────────────────────────────────────────────────────────────────

resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${local.prefix}-ecs-"
  description = "ECS tasks - allow traffic from ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "From ALB"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Allow tasks to talk to each other (API <-> workers via Redis)
  ingress {
    description = "Self"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle { create_before_destroy = true }

  tags = { Name = "${local.prefix}-ecs-sg" }
}

# ── RDS ──────────────────────────────────────────────────────────────────────

resource "aws_security_group" "rds" {
  name_prefix = "${local.prefix}-rds-"
  description = "RDS PostgreSQL - allow from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "PostgreSQL from ECS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle { create_before_destroy = true }

  tags = { Name = "${local.prefix}-rds-sg" }
}

# ── ElastiCache ──────────────────────────────────────────────────────────────

resource "aws_security_group" "redis" {
  name_prefix = "${local.prefix}-redis-"
  description = "ElastiCache Redis - allow from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Redis from ECS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  lifecycle { create_before_destroy = true }

  tags = { Name = "${local.prefix}-redis-sg" }
}
