from __future__ import annotations

import boto3
from botocore.config import Config

from app.core.settings import settings


def _build_s3_kwargs(endpoint_url: str | None = None) -> dict:
    """Build kwargs for boto3 S3 client. Uses IAM role when no explicit keys."""
    kwargs: dict = {"region_name": settings.S3_REGION}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    if settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY:
        kwargs["aws_access_key_id"] = settings.S3_ACCESS_KEY
        kwargs["aws_secret_access_key"] = settings.S3_SECRET_KEY
    if settings.S3_USE_PATH_STYLE:
        kwargs["config"] = Config(s3={"addressing_style": "path"})
    return kwargs


def _get_s3_client():
    return boto3.client("s3", **_build_s3_kwargs(settings.S3_ENDPOINT_URL or None))


def _get_public_s3_client():
    """S3 client using the public endpoint URL for browser-facing presigned URLs."""
    endpoint = settings.S3_PUBLIC_ENDPOINT_URL or settings.S3_ENDPOINT_URL or None
    return boto3.client("s3", **_build_s3_kwargs(endpoint))


def presign_put_url(key: str, content_type: str = "application/octet-stream", expires: int = 3600) -> str:
    s3 = _get_public_s3_client()
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presign_get_url(key: str, expires: int = 3600) -> str:
    s3 = _get_public_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(key: str) -> None:
    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
