from __future__ import annotations

import logging

import boto3
from botocore.exceptions import ClientError

from app.core.settings import settings

logger = logging.getLogger(__name__)


def ensure_s3_bucket() -> None:
    """Create the S3/MinIO bucket if it does not exist."""
    client_kwargs: dict = {
        "endpoint_url": settings.S3_ENDPOINT_URL or None,
        "aws_access_key_id": settings.S3_ACCESS_KEY,
        "aws_secret_access_key": settings.S3_SECRET_KEY,
        "region_name": settings.S3_REGION,
    }
    if settings.S3_USE_PATH_STYLE:
        from botocore.config import Config
        client_kwargs["config"] = Config(s3={"addressing_style": "path"})

    s3 = boto3.client("s3", **client_kwargs)
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET)
        logger.info("S3 bucket '%s' already exists", settings.S3_BUCKET)
    except ClientError:
        s3.create_bucket(
            Bucket=settings.S3_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": settings.S3_REGION},
        )
        logger.info("Created S3 bucket '%s'", settings.S3_BUCKET)
