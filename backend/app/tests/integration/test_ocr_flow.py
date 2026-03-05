"""Integration tests: OCR job creation, listing, and retrieval."""
from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_ocr_data(db):
    """Clean up ocr_jobs before each test."""
    await db.execute(text("DELETE FROM ocr_jobs WHERE tenant_id = :tid"), {"tid": TID})
    await db.commit()
    yield


@pytest.mark.asyncio
async def test_create_ocr_job(client: AsyncClient):
    """POST /v1/ocr/jobs with s3_key and file_name returns 201."""
    with patch("app.infra.celery_app.celery_app.send_task"):
        resp = await client.post("/v1/ocr/jobs", json={
            "s3_key": f"{TID}/ocr/test-doc.pdf",
            "file_name": "test-doc.pdf",
        })
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] is not None
    assert data["s3_key"] == f"{TID}/ocr/test-doc.pdf"
    assert data["file_name"] == "test-doc.pdf"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_list_ocr_jobs(client: AsyncClient, db):
    """Seed an ocr_job via SQL, GET /v1/ocr/jobs, verify it appears."""
    job_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO ocr_jobs (id, tenant_id, s3_key, file_name, status, provider, created_at)
        VALUES (:id, :tid, :s3, :fname, 'pending', 'MOCK', NOW())
        ON CONFLICT DO NOTHING
    """), {
        "id": job_id,
        "tid": TID,
        "s3": f"{TID}/ocr/seeded.pdf",
        "fname": "seeded.pdf",
    })
    await db.commit()

    resp = await client.get("/v1/ocr/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    ids = [j["id"] for j in data]
    assert job_id in ids


@pytest.mark.asyncio
async def test_get_ocr_job(client: AsyncClient, db):
    """Seed an ocr_job, GET /v1/ocr/jobs/{id}, verify fields."""
    job_id = str(uuid.uuid4())
    s3_key = f"{TID}/ocr/detail-test.pdf"
    await db.execute(text("""
        INSERT INTO ocr_jobs (id, tenant_id, s3_key, file_name, status, provider, created_at)
        VALUES (:id, :tid, :s3, :fname, 'completed', 'MOCK', NOW())
        ON CONFLICT DO NOTHING
    """), {
        "id": job_id,
        "tid": TID,
        "s3": s3_key,
        "fname": "detail-test.pdf",
    })
    await db.commit()

    resp = await client.get(f"/v1/ocr/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert data["s3_key"] == s3_key
    assert data["file_name"] == "detail-test.pdf"
    assert data["status"] == "completed"
    assert data["provider"] == "MOCK"
