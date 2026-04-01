"""Structured JSON logging configuration for production.

Outputs one JSON object per log line to stdout — compatible with
CloudWatch Logs Insights queries like:
    fields @timestamp, level, message, tenant_id, request_id
    | filter level = "ERROR"
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Merge structured extra fields from CorrelationIdMiddleware / tasks
        for key in ("request_id", "tenant_id", "method", "path", "status", "duration_ms"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val

        if record.exc_info and record.exc_info[1]:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Replace root handler with a JSON handler writing to stdout."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Remove any existing handlers (e.g. uvicorn defaults)
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
