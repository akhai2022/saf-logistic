"""Integration tests for the bulk import module (drivers, vehicles, CSV/Excel)."""
from __future__ import annotations

import io
import os
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.tests.conftest import ADMIN_ID, TENANT_ID, TENANT_B_ID


FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures")


def _read_fixture(name: str) -> bytes:
    """Read a fixture file as bytes."""
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, "rb") as f:
        return f.read()


def _make_csv_bytes(content: str) -> bytes:
    """Helper to create CSV bytes from a string (semicolon-delimited)."""
    return content.encode("utf-8-sig")


# ══════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_upload_csv(client: AsyncClient):
    """Upload a CSV file and verify the import job is created."""
    content = _read_fixture("import_drivers_ok.csv")

    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers.csv", content, "text/csv")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["entity_type"] == "driver"
    assert data["status"] == "uploaded"
    assert data["file_name"] == "drivers.csv"
    assert data["id"]


@pytest.mark.asyncio
async def test_import_upload_rejects_invalid_entity_type(client: AsyncClient):
    """Upload with an invalid entity_type returns 400."""
    content = b"header1;header2\nval1;val2"
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "invalid_type"},
        files={"file": ("test.csv", content, "text/csv")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_import_upload_rejects_empty_file(client: AsyncClient):
    """Upload with an empty file returns 400."""
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("empty.csv", b"", "text/csv")},
    )
    assert resp.status_code == 400


# ══════════════════════════════════════════════════════════════════
# PREVIEW
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_preview_drivers(client: AsyncClient):
    """Preview a valid drivers CSV: all rows should be valid."""
    content = _read_fixture("import_drivers_ok.csv")

    # Upload
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers.csv", content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Preview
    resp = await client.post(f"/v1/imports/{job_id}/preview")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["entity_type"] == "driver"
    assert data["total_rows"] == 5
    assert data["valid_rows"] == 5
    assert data["error_rows"] == 0
    assert len(data["errors"]) == 0
    assert len(data["sample_rows"]) == 5
    assert "detected_mapping" in data

    # Verify mapping detected French headers
    mapping = data["detected_mapping"]
    assert mapping.get("Nom") == "nom"
    assert mapping.get("Prénom") == "prenom"
    assert mapping.get("Matricule") == "matricule"


@pytest.mark.asyncio
async def test_import_preview_with_errors(client: AsyncClient):
    """Preview a CSV with validation errors."""
    csv_content = _make_csv_bytes(
        "Matricule;Nom;Prénom;Type contrat\n"
        "ERR-001;Dupont;Jean;CDI\n"
        "ERR-002;;Pierre;INVALID_TYPE\n"  # Missing nom + invalid type_contrat
        "ERR-003;Bernard;Luc;CDD\n"
    )

    # Upload
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers_err.csv", csv_content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Preview
    resp = await client.post(f"/v1/imports/{job_id}/preview")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["total_rows"] == 3
    assert data["valid_rows"] == 2
    assert data["error_rows"] == 1
    assert len(data["errors"]) >= 1

    # Check error points to row 3 (the invalid row)
    error_rows = {e["row"] for e in data["errors"]}
    assert 3 in error_rows


@pytest.mark.asyncio
async def test_import_preview_with_custom_mapping(client: AsyncClient):
    """Preview using a user-provided column mapping."""
    csv_content = _make_csv_bytes(
        "ID;Family Name;First Name\n"
        "CUST-001;Dupont;Jean\n"
        "CUST-002;Martin;Pierre\n"
    )

    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("custom_map.csv", csv_content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Preview with custom mapping
    resp = await client.post(
        f"/v1/imports/{job_id}/preview",
        json={"column_mapping": {
            "ID": "matricule",
            "Family Name": "nom",
            "First Name": "prenom",
        }},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["valid_rows"] == 2


# ══════════════════════════════════════════════════════════════════
# APPLY
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_apply_drivers(client: AsyncClient, db: AsyncSession):
    """Apply a valid drivers CSV: rows should be inserted."""
    content = _read_fixture("import_drivers_ok.csv")

    # Upload
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers.csv", content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Preview first (optional but realistic)
    resp = await client.post(f"/v1/imports/{job_id}/preview")
    assert resp.status_code == 200

    # Apply
    resp = await client.post(f"/v1/imports/{job_id}/apply")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["entity_type"] == "driver"
    assert data["total_rows"] == 5
    assert data["inserted_rows"] + data["updated_rows"] == 5
    assert data["skipped_rows"] == 0

    # Verify driver exists in DB
    result = await db.execute(
        text("SELECT * FROM drivers WHERE tenant_id = :tid AND matricule = 'IMP-D001'"),
        {"tid": str(TENANT_ID)},
    )
    driver = result.first()
    assert driver is not None
    assert driver.nom == "Dupont"
    assert driver.prenom == "Jean"

    # Verify the job status is 'applied'
    resp = await client.get(f"/v1/imports/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "applied"


@pytest.mark.asyncio
async def test_import_vehicle_upsert(client: AsyncClient, db: AsyncSession):
    """Import vehicles twice: first insert, second should update (upsert)."""
    content = _read_fixture("import_vehicles_ok.csv")

    # First import: upload + apply
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "vehicle"},
        files={"file": ("vehicles.csv", content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id_1 = resp.json()["id"]

    resp = await client.post(f"/v1/imports/{job_id_1}/apply")
    assert resp.status_code == 200, resp.text
    data_1 = resp.json()
    assert data_1["inserted_rows"] == 5

    # Verify vehicle in DB
    result = await db.execute(
        text("SELECT * FROM vehicles WHERE tenant_id = :tid AND immatriculation = 'AA-100-BB'"),
        {"tid": str(TENANT_ID)},
    )
    vehicle = result.first()
    assert vehicle is not None
    assert vehicle.marque == "Renault"

    # Second import: same file -> should update, not insert
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "vehicle"},
        files={"file": ("vehicles2.csv", content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id_2 = resp.json()["id"]

    resp = await client.post(f"/v1/imports/{job_id_2}/apply")
    assert resp.status_code == 200, resp.text
    data_2 = resp.json()

    assert data_2["updated_rows"] == 5
    assert data_2["inserted_rows"] == 0


@pytest.mark.asyncio
async def test_import_apply_rejects_double_apply(client: AsyncClient):
    """Applying the same import job twice should return an error."""
    content = _read_fixture("import_drivers_ok.csv")

    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers.csv", content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # First apply
    resp = await client.post(f"/v1/imports/{job_id}/apply")
    assert resp.status_code == 200

    # Second apply should fail
    resp = await client.post(f"/v1/imports/{job_id}/apply")
    assert resp.status_code == 400
    assert "deja ete applique" in resp.json()["detail"]


# ══════════════════════════════════════════════════════════════════
# TENANT ISOLATION
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_tenant_isolation(
    client: AsyncClient,
    client_tenant_b: AsyncClient,
):
    """Import job created by Tenant A is not accessible by Tenant B."""
    content = _read_fixture("import_drivers_ok.csv")

    # Upload as Tenant A
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers.csv", content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Tenant A can see it
    resp = await client.get(f"/v1/imports/{job_id}")
    assert resp.status_code == 200

    # Tenant B gets 404
    resp = await client_tenant_b.get(f"/v1/imports/{job_id}")
    assert resp.status_code == 404

    # Tenant B cannot preview
    resp = await client_tenant_b.post(f"/v1/imports/{job_id}/preview")
    assert resp.status_code == 400 or resp.status_code == 404

    # Tenant B cannot apply
    resp = await client_tenant_b.post(f"/v1/imports/{job_id}/apply")
    assert resp.status_code == 400 or resp.status_code == 404


# ══════════════════════════════════════════════════════════════════
# ERRORS CSV DOWNLOAD
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_errors_csv_download(client: AsyncClient):
    """Download errors CSV after previewing a file with errors."""
    csv_content = _make_csv_bytes(
        "Matricule;Nom;Prénom;Type contrat\n"
        "ERR-CSV-001;Dupont;Jean;CDI\n"
        "ERR-CSV-002;;Pierre;INVALID_TYPE\n"  # Missing nom + invalid type
        "ERR-CSV-003;Bernard;Luc;CDD\n"
    )

    # Upload
    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers_err.csv", csv_content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Preview (generates errors)
    resp = await client.post(f"/v1/imports/{job_id}/preview")
    assert resp.status_code == 200
    assert resp.json()["error_rows"] > 0

    # Download errors CSV
    resp = await client.get(f"/v1/imports/{job_id}/errors-csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")

    # Parse the CSV content
    csv_text = resp.content.decode("utf-8-sig")
    lines = csv_text.strip().split("\n")
    assert len(lines) >= 2  # header + at least 1 error row
    assert "Ligne" in lines[0]
    assert "Message" in lines[0]


@pytest.mark.asyncio
async def test_import_errors_csv_empty_when_no_errors(client: AsyncClient):
    """Errors CSV for a valid import should only have the header row."""
    content = _read_fixture("import_drivers_ok.csv")

    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("drivers.csv", content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Preview (no errors expected)
    resp = await client.post(f"/v1/imports/{job_id}/preview")
    assert resp.status_code == 200
    assert resp.json()["error_rows"] == 0

    # Download errors CSV
    resp = await client.get(f"/v1/imports/{job_id}/errors-csv")
    assert resp.status_code == 200
    csv_text = resp.content.decode("utf-8-sig")
    lines = csv_text.strip().split("\n")
    assert len(lines) == 1  # header only


# ══════════════════════════════════════════════════════════════════
# GET JOB
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_get_nonexistent_job(client: AsyncClient):
    """Getting a nonexistent import job returns 404."""
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/v1/imports/{fake_id}")
    assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════
# FRENCH DATE & DECIMAL PARSING
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_import_french_date_parsing(client: AsyncClient, db: AsyncSession):
    """French dates DD/MM/YYYY should be correctly parsed."""
    csv_content = _make_csv_bytes(
        "Matricule;Nom;Prénom;Date de naissance;Date d'entrée\n"
        "IMP-FR-001;Lefevre;Antoine;25/12/1990;01/06/2020\n"
    )

    resp = await client.post(
        "/v1/imports/upload",
        params={"entity_type": "driver"},
        files={"file": ("french_dates.csv", csv_content, "text/csv")},
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    resp = await client.post(f"/v1/imports/{job_id}/apply")
    assert resp.status_code == 200, resp.text
    assert resp.json()["inserted_rows"] + resp.json()["updated_rows"] == 1

    # Verify in DB
    result = await db.execute(
        text("SELECT date_naissance, date_entree FROM drivers WHERE tenant_id = :tid AND matricule = 'IMP-FR-001'"),
        {"tid": str(TENANT_ID)},
    )
    row = result.first()
    assert row is not None
    assert str(row.date_naissance) == "1990-12-25"
    assert str(row.date_entree) == "2020-06-01"
