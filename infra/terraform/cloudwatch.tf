# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.prefix}/api"
  retention_in_days = var.environment == "prod" ? 90 : 14

  tags = { Name = "${local.prefix}-api-logs" }
}

resource "aws_cloudwatch_log_group" "worker_default" {
  name              = "/ecs/${local.prefix}/worker-default"
  retention_in_days = var.environment == "prod" ? 90 : 14

  tags = { Name = "${local.prefix}-worker-default-logs" }
}

resource "aws_cloudwatch_log_group" "worker_ocr" {
  name              = "/ecs/${local.prefix}/worker-ocr"
  retention_in_days = var.environment == "prod" ? 90 : 14

  tags = { Name = "${local.prefix}-worker-ocr-logs" }
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${local.prefix}/frontend"
  retention_in_days = var.environment == "prod" ? 90 : 14

  tags = { Name = "${local.prefix}-frontend-logs" }
}
