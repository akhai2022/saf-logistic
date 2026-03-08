# -----------------------------------------------------------------------------
# Route53 Hosted Zone + DNS Records + ACM Validation
# -----------------------------------------------------------------------------

# ── Hosted Zone ──────────────────────────────────────────────────────────────

resource "aws_route53_zone" "main" {
  count = var.domain_name != "" ? 1 : 0
  name  = var.domain_name

  tags = { Name = "${local.prefix}-zone" }
}

# ── ACM Certificate DNS Validation Records ───────────────────────────────────

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in(var.domain_name != "" ? aws_acm_certificate.main[0].domain_validation_options : []) :
    dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id         = aws_route53_zone.main[0].zone_id
  name            = each.value.name
  type            = each.value.type
  ttl             = 300
  records         = [each.value.record]
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "main" {
  count                   = var.domain_name != "" ? 1 : 0
  certificate_arn         = aws_acm_certificate.main[0].arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# ── A Record — root domain → ALB ────────────────────────────────────────────

resource "aws_route53_record" "app" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# ── A Record — www subdomain → ALB ──────────────────────────────────────────

resource "aws_route53_record" "www" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}
