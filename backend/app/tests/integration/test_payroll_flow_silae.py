"""Integration test: payroll CSV import → SILAE export."""
from __future__ import annotations

import os
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import text

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


@pytest.mark.asyncio
async def test_payroll_import_export(client: AsyncClient, db):
    """
    1. Seed driver + variable types + mappings
    2. Create payroll period
    3. Import CSV
    4. Export SILAE
    5. Verify export matches expected
    """
    tid = "00000000-0000-0000-0000-000000000001"

    # Seed driver
    driver_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO drivers (id, tenant_id, matricule, first_name, last_name)
        VALUES (:id, :tid, 'SAF-001', 'Jean', 'Dupont')
        ON CONFLICT ON CONSTRAINT uq_drivers_tenant_matricule DO NOTHING
    """), {"id": driver_id, "tid": tid})

    # Seed variable types
    vt_heures_id = str(uuid.uuid4())
    vt_panier_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO payroll_variable_types (id, tenant_id, code, label, unit, category)
        VALUES (:id, :tid, 'heures_normales', 'Heures normales', 'h', 'temps')
        ON CONFLICT ON CONSTRAINT uq_payvar_types_tenant_code DO NOTHING
    """), {"id": vt_heures_id, "tid": tid})
    await db.execute(text("""
        INSERT INTO payroll_variable_types (id, tenant_id, code, label, unit, category)
        VALUES (:id, :tid, 'prime_panier', 'Prime de panier', 'j', 'prime')
        ON CONFLICT ON CONSTRAINT uq_payvar_types_tenant_code DO NOTHING
    """), {"id": vt_panier_id, "tid": tid})

    # Seed SILAE mappings
    await db.execute(text("""
        INSERT INTO payroll_mappings (id, tenant_id, variable_type_code, target_code, target_label)
        VALUES (:id, :tid, 'heures_normales', '0100', 'Heures normales')
        ON CONFLICT ON CONSTRAINT uq_paymap_tenant_varcode DO NOTHING
    """), {"id": str(uuid.uuid4()), "tid": tid})
    await db.execute(text("""
        INSERT INTO payroll_mappings (id, tenant_id, variable_type_code, target_code, target_label)
        VALUES (:id, :tid, 'prime_panier', '0300', 'Panier')
        ON CONFLICT ON CONSTRAINT uq_paymap_tenant_varcode DO NOTHING
    """), {"id": str(uuid.uuid4()), "tid": tid})
    await db.commit()

    # 1. Create period
    resp = await client.post("/v1/payroll/periods?year=2024&month=3")
    assert resp.status_code in (201, 409)  # 409 if already exists
    if resp.status_code == 201:
        period_id = resp.json()["id"]
    else:
        periods = await client.get("/v1/payroll/periods")
        period_id = next(p["id"] for p in periods.json() if p["year"] == 2024 and p["month"] == 3)

    # 2. Import CSV
    csv_path = os.path.join(FIXTURES_DIR, "payroll_import_ok.csv")
    with open(csv_path, "rb") as f:
        resp = await client.post(
            f"/v1/payroll/periods/{period_id}/import-csv",
            files={"file": ("payroll.csv", f, "text/csv")},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] >= 2
    assert len(data["errors"]) == 0

    # 3. Get variables
    resp = await client.get(f"/v1/payroll/periods/{period_id}/variables")
    assert resp.status_code == 200
    variables = resp.json()
    assert len(variables) >= 2

    # 4. Export SILAE
    resp = await client.get(f"/v1/payroll/periods/{period_id}/export-silae")
    assert resp.status_code == 200
    export_content = resp.text
    assert "0100" in export_content  # heures_normales mapped code
    assert "0300" in export_content  # prime_panier mapped code
    assert "SAF-001" in export_content
