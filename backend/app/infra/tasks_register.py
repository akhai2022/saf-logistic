"""Celery worker entry-point — import all tasks so they get registered."""
from app.infra.celery_app import celery_app  # noqa: F401
from app.infra import tasks  # noqa: F401
