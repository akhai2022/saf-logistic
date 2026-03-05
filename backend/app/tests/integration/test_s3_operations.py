"""Integration tests for S3/MinIO operations — verifies real object storage works."""
from __future__ import annotations

import uuid

import pytest

from app.infra.s3 import _get_s3_client, presign_get_url, presign_put_url, delete_object
from app.core.settings import settings


@pytest.fixture(autouse=True)
def _cleanup_s3_keys():
    """Track and clean up test S3 keys after each test."""
    keys: list[str] = []
    yield keys
    s3 = _get_s3_client()
    for key in keys:
        try:
            s3.delete_object(Bucket=settings.S3_BUCKET, Key=key)
        except Exception:
            pass


def test_put_and_get_object(_cleanup_s3_keys):
    """Upload bytes to S3, download, verify they match."""
    s3 = _get_s3_client()
    key = f"test/{uuid.uuid4()}.txt"
    _cleanup_s3_keys.append(key)
    content = b"Hello from integration test"

    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=content, ContentType="text/plain")

    resp = s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
    downloaded = resp["Body"].read()
    assert downloaded == content


def test_presign_put_url(_cleanup_s3_keys):
    """Generate a presigned PUT URL — should be a valid URL string."""
    key = f"test/{uuid.uuid4()}.pdf"
    _cleanup_s3_keys.append(key)

    url = presign_put_url(key, content_type="application/pdf")
    assert isinstance(url, str)
    assert "saf-docs" in url or key in url
    assert url.startswith("http")


def test_presign_get_url(_cleanup_s3_keys):
    """Upload an object, then generate a presigned GET URL."""
    s3 = _get_s3_client()
    key = f"test/{uuid.uuid4()}.txt"
    _cleanup_s3_keys.append(key)

    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=b"test content")

    url = presign_get_url(key)
    assert isinstance(url, str)
    assert url.startswith("http")


def test_delete_object(_cleanup_s3_keys):
    """Upload, delete, verify object is gone."""
    s3 = _get_s3_client()
    key = f"test/{uuid.uuid4()}.txt"

    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=b"to be deleted")

    delete_object(key)

    from botocore.exceptions import ClientError
    with pytest.raises(ClientError):
        s3.get_object(Bucket=settings.S3_BUCKET, Key=key)
