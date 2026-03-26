# ──────────────────────────────────────────────
# General
# ──────────────────────────────────────────────
variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "saf-logistic"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# ──────────────────────────────────────────────
# Existing Infrastructure References
# ──────────────────────────────────────────────
variable "existing_vpc_id" {
  description = "ID of the existing VPC"
  type        = string
}

variable "existing_private_subnet_ids" {
  description = "IDs of existing private subnets for ECS tasks"
  type        = list(string)
}

variable "existing_public_subnet_ids" {
  description = "IDs of existing public subnets"
  type        = list(string)
}

variable "existing_rds_endpoint" {
  description = "Endpoint of the shared RDS instance (host:port)"
  type        = string
}

variable "existing_rds_security_group_id" {
  description = "Security group ID of the shared RDS instance"
  type        = string
}

variable "existing_ecs_cluster_arn" {
  description = "ARN of the shared ECS cluster"
  type        = string
}

variable "existing_alb_name" {
  description = "Name of the Formation ALB to attach to"
  type        = string
}

variable "existing_alb_security_group_id" {
  description = "Security group ID of the Formation ALB"
  type        = string
}

variable "existing_redis_url" {
  description = "Redis endpoint URL (without DB number), e.g. redis://host:6379"
  type        = string
}

# ──────────────────────────────────────────────
# Domain & Routing
# ──────────────────────────────────────────────
variable "domain_name" {
  description = "Root domain name (must match Formation's Route53 zone)"
  type        = string
  default     = "dataforgeai.fr"
}

variable "web_subdomain" {
  description = "Subdomain for the web frontend"
  type        = string
  default     = "saf"
}

variable "api_subdomain" {
  description = "Subdomain for the API"
  type        = string
  default     = "api-saf"
}

variable "listener_rule_priority_api" {
  description = "Priority for the API listener rule on the Formation ALB"
  type        = number
  default     = 30
}

variable "listener_rule_priority_web" {
  description = "Priority for the Web listener rule on the Formation ALB"
  type        = number
  default     = 35
}

# ──────────────────────────────────────────────
# Redis DB numbers (shared ElastiCache)
# ──────────────────────────────────────────────
variable "redis_db_broker" {
  description = "Redis DB number for Celery broker"
  type        = number
  default     = 3
}

variable "redis_db_result" {
  description = "Redis DB number for Celery result backend"
  type        = number
  default     = 4
}

# ──────────────────────────────────────────────
# ECS — API Service
# ──────────────────────────────────────────────
variable "api_cpu" {
  description = "CPU units for the API task (1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "api_memory" {
  description = "Memory (MiB) for the API task"
  type        = number
  default     = 512
}

variable "api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 1
}

# ──────────────────────────────────────────────
# ECS — Web Service
# ──────────────────────────────────────────────
variable "web_cpu" {
  description = "CPU units for the Web task"
  type        = number
  default     = 256
}

variable "web_memory" {
  description = "Memory (MiB) for the Web task"
  type        = number
  default     = 512
}

variable "web_desired_count" {
  description = "Desired number of Web tasks"
  type        = number
  default     = 1
}

# ──────────────────────────────────────────────
# ECS — Worker Service
# ──────────────────────────────────────────────
variable "worker_cpu" {
  description = "CPU units for the Worker task"
  type        = number
  default     = 256
}

variable "worker_memory" {
  description = "Memory (MiB) for the Worker task"
  type        = number
  default     = 512
}

variable "worker_desired_count" {
  description = "Desired number of Worker tasks"
  type        = number
  default     = 1
}

# ──────────────────────────────────────────────
# Tags
# ──────────────────────────────────────────────
variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
