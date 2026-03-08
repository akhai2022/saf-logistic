# -----------------------------------------------------------------------------
# Variables — SAF-Logistic AWS Infrastructure
# -----------------------------------------------------------------------------

variable "project" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "saf-logistic"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

# ── Networking ───────────────────────────────────────────────────────────────

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability zones"
  type        = list(string)
  default     = ["eu-west-3a", "eu-west-3b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

# ── RDS ──────────────────────────────────────────────────────────────────────

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "saf"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "saf"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

# ── ElastiCache ──────────────────────────────────────────────────────────────

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro"
}

# ── ECS ──────────────────────────────────────────────────────────────────────

variable "api_cpu" {
  description = "CPU units for API task (1024 = 1 vCPU)"
  type        = number
  default     = 512
}

variable "api_memory" {
  description = "Memory in MiB for API task"
  type        = number
  default     = 1024
}

variable "api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 2
}

variable "worker_default_cpu" {
  description = "CPU units for default Celery worker"
  type        = number
  default     = 256
}

variable "worker_default_memory" {
  description = "Memory in MiB for default Celery worker"
  type        = number
  default     = 512
}

variable "worker_ocr_cpu" {
  description = "CPU units for OCR Celery worker"
  type        = number
  default     = 1024
}

variable "worker_ocr_memory" {
  description = "Memory in MiB for OCR Celery worker"
  type        = number
  default     = 2048
}

variable "frontend_cpu" {
  description = "CPU units for frontend task"
  type        = number
  default     = 256
}

variable "frontend_memory" {
  description = "Memory in MiB for frontend task"
  type        = number
  default     = 512
}

variable "frontend_desired_count" {
  description = "Desired number of frontend tasks"
  type        = number
  default     = 2
}

# ── Application ──────────────────────────────────────────────────────────────

variable "app_secret_key" {
  description = "Application secret key for JWT signing"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the application (optional, used for ACM/Route53)"
  type        = string
  default     = ""
}

# ── Tags ─────────────────────────────────────────────────────────────────────

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}
