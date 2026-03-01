from __future__ import annotations

import boto3
from botocore.config import Config

from app.core.settings import settings


def _get_s3_client():
    kwargs: dict = {
        "endpoint_url": settings.S3_ENDPOINT_URL or None,
        "aws_access_key_id": settings.S3_ACCESS_KEY,
        "aws_secret_access_key": settings.S3_SECRET_KEY,
        "region_name": settings.S3_REGION,
    }
    if settings.S3_USE_PATH_STYLE:
        kwargs["config"] = Config(s3={"addressing_style": "path"})
    return boto3.client("s3", **kwargs)


def presign_put_url(key: str, content_type: str = "application/octet-stream", expires: int = 3600) -> str:
    s3 = _get_s3_client()
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )


def presign_get_url(key: str, expires: int = 3600) -> str:
    s3 = _get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )


def delete_object(key: str) -> None:
    s3 = _get_s3_client()
    s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
