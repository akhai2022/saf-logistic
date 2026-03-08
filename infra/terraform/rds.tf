# -----------------------------------------------------------------------------
# RDS PostgreSQL 16
# -----------------------------------------------------------------------------

resource "aws_db_subnet_group" "main" {
  name       = "${local.prefix}-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${local.prefix}-db-subnet" }
}

resource "aws_db_instance" "postgres" {
  identifier     = "${local.prefix}-postgres"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az            = var.environment == "prod" ? true : false
  publicly_accessible = false
  skip_final_snapshot = var.environment != "prod"

  final_snapshot_identifier = var.environment == "prod" ? "${local.prefix}-final-snapshot" : null

  backup_retention_period = var.environment == "prod" ? 7 : 1

  tags = { Name = "${local.prefix}-postgres" }
}
