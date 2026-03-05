"""Integration tests: file presign endpoints and reports dashboard."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_reports_data(db):
    """Clean up data that could interfere with KPI calculations."""
    # No aggressive cleanup needed; KPIs are aggregation queries.
    # Just yield to satisfy the autouse pattern.
    yield


# ======================================================================
# File presign endpoints
# ======================================================================


@pytest.mark.asyncio
async def test_presign_upload_url(client: AsyncClient):
    """POST /v1/files/presign-upload returns an upload_url and s3_key."""
    resp = await client.post("/v1/files/presign-upload", json={
        "file_name": "invoice-scan.pdf",
        "content_type": "application/pdf",
        "entity_type": "ocr",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "upload_url" in data
    assert "s3_key" in data
    assert data["upload_url"].startswith("http")
    assert data["s3_key"].startswith(TID)
    assert data["s3_key"].endswith(".pdf")


@pytest.mark.asyncio
async def test_presign_download_url(client: AsyncClient):
    """GET /v1/files/presign-download with an s3_key returns a download_url."""
    s3_key = f"{TID}/ocr/some-document.pdf"
    resp = await client.get("/v1/files/presign-download", params={"s3_key": s3_key})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "download_url" in data
    assert data["download_url"].startswith("http")


# ======================================================================
# Reports / KPI dashboard
# ======================================================================


@pytest.mark.asyncio
async def test_kpis_endpoint(client: AsyncClient):
    """GET /v1/reports/dashboard returns 200 with role and kpis keys."""
    resp = await client.get("/v1/reports/dashboard")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "role" in data
    assert "kpis" in data
    assert isinstance(data["kpis"], list)

    # Admin role should get the full set of KPIs
    assert data["role"] == "admin"
    kpi_keys = [kpi["key"] for kpi in data["kpis"]]
    # Verify at least a few expected admin KPI keys are present
    for expected in ["ca_mensuel", "marge", "missions_en_cours", "litiges_ouverts"]:
        assert expected in kpi_keys, f"Expected KPI key '{expected}' not found in {kpi_keys}"

    # Each KPI should have key, label, value
    for kpi in data["kpis"]:
        assert "key" in kpi
        assert "label" in kpi
        assert "value" in kpi
