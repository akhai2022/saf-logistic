from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    DATABASE_URL: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "postgresql+asyncpg://saf:saf@localhost:5432/saf"
        )
    )
    CELERY_BROKER_URL: str = field(
        default_factory=lambda: os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    )
    CELERY_RESULT_BACKEND: str = field(
        default_factory=lambda: os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    )
    APP_SECRET_KEY: str = field(
        default_factory=lambda: os.getenv("APP_SECRET_KEY", "dev-secret-change-in-prod")
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8h

    S3_ENDPOINT_URL: str = field(
        default_factory=lambda: os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
    )
    S3_ACCESS_KEY: str = field(default_factory=lambda: os.getenv("S3_ACCESS_KEY", "minio"))
    S3_SECRET_KEY: str = field(default_factory=lambda: os.getenv("S3_SECRET_KEY", "minio12345"))
    S3_BUCKET: str = field(default_factory=lambda: os.getenv("S3_BUCKET", "saf-docs"))
    S3_REGION: str = field(default_factory=lambda: os.getenv("S3_REGION", "eu-west-3"))
    S3_USE_PATH_STYLE: bool = field(
        default_factory=lambda: os.getenv("S3_USE_PATH_STYLE", "true").lower() == "true"
    )

    OCR_PROVIDER: str = field(default_factory=lambda: os.getenv("OCR_PROVIDER", "MOCK"))


settings = Settings()
