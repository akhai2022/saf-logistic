# -----------------------------------------------------------------------------
# Application Load Balancer
# -----------------------------------------------------------------------------

resource "aws_lb" "main" {
  name               = "${local.prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = { Name = "${local.prefix}-alb" }
}

# ── ACM Certificate (when domain is provided) ───────────────────────────────

resource "aws_acm_certificate" "main" {
  count             = var.domain_name != "" ? 1 : 0
  domain_name       = var.domain_name
  validation_method = "DNS"

  subject_alternative_names = [
    "*.${var.domain_name}",
  ]

  lifecycle { create_before_destroy = true }

  tags = { Name = "${local.prefix}-cert" }
}

# ── Target Groups ────────────────────────────────────────────────────────────

resource "aws_lb_target_group" "api" {
  name        = "${local.prefix}-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/health"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = { Name = "${local.prefix}-api-tg" }
}

resource "aws_lb_target_group" "frontend" {
  name        = "${local.prefix}-fe-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = { Name = "${local.prefix}-frontend-tg" }
}

# ── HTTPS Listener (when domain + cert are available) ────────────────────────

resource "aws_lb_listener" "https" {
  count             = var.domain_name != "" ? 1 : 0
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.main[0].certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

# Route /v1/* /health /docs /openapi.json → backend (HTTPS)
resource "aws_lb_listener_rule" "api_https" {
  count        = var.domain_name != "" ? 1 : 0
  listener_arn = aws_lb_listener.https[0].arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/v1/*", "/health", "/docs", "/openapi.json"]
    }
  }
}

# ── HTTP Listener — redirect to HTTPS when cert exists, forward otherwise ───

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = var.domain_name != "" ? "redirect" : "forward"

    # Forward to frontend when no domain/cert (dev mode)
    dynamic "forward" {
      for_each = var.domain_name == "" ? [1] : []
      content {
        target_group {
          arn = aws_lb_target_group.frontend.arn
        }
      }
    }

    # Redirect HTTP → HTTPS when domain is set (staging/prod)
    dynamic "redirect" {
      for_each = var.domain_name != "" ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }
}

# Route /v1/* /health /docs /openapi.json → backend (HTTP, dev only)
resource "aws_lb_listener_rule" "api_http" {
  count        = var.domain_name == "" ? 1 : 0
  listener_arn = aws_lb_listener.http.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/v1/*", "/health", "/docs", "/openapi.json"]
    }
  }
}
