"""Integration tests: billing invoices pagination, credit notes, supplier invoices, dunning."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"


@pytest_asyncio.fixture(autouse=True)
async def clean_billing_extended_data(db):
    """Clean up billing-related data before each test."""
    # Delete in FK dependency order
    await db.execute(text("DELETE FROM subcontractor_offers WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM tasks WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dunning_actions WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dunning_levels WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM credit_note_lines WHERE credit_note_id IN (SELECT id FROM credit_notes WHERE tenant_id = :tid)"), {"tid": TID})
    await db.execute(text("DELETE FROM credit_notes WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM supplier_invoices WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text(
        "DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE tenant_id = :tid)"
    ), {"tid": TID})
    await db.execute(text("DELETE FROM invoices WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM pricing_rules WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dispute_attachments WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM disputes WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM jobs WHERE tenant_id = :tid"), {"tid": TID})
    await db.commit()
    yield


# ══════════════════════════════════════════════════════════════════
# Invoices — Pagination
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_invoices_pagination(client: AsyncClient, db):
    """Create 2 invoices via raw SQL, verify limit/offset pagination works."""
    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name, payment_terms_days)
        VALUES (:id, :tid, 'Pagination Client', 30)
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    inv_id_1 = str(uuid.uuid4())
    inv_id_2 = str(uuid.uuid4())
    today = date.today()
    due = today + timedelta(days=30)

    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, status, issue_date, due_date,
                              total_ht, tva_rate, total_tva, total_ttc)
        VALUES (:id, :tid, :cid, 'draft', :idate, :ddate, 100.0, 20.0, 20.0, 120.0)
    """), {"id": inv_id_1, "tid": TID, "cid": cust_id, "idate": today, "ddate": due})

    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, status, issue_date, due_date,
                              total_ht, tva_rate, total_tva, total_ttc)
        VALUES (:id, :tid, :cid, 'draft', :idate, :ddate, 200.0, 20.0, 40.0, 240.0)
    """), {"id": inv_id_2, "tid": TID, "cid": cust_id, "idate": today, "ddate": due})
    await db.commit()

    # Page 1: limit=1
    resp = await client.get("/v1/billing/invoices", params={"limit": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1

    # Page 2: offset=1, limit=1
    resp = await client.get("/v1/billing/invoices", params={"limit": 1, "offset": 1})
    assert resp.status_code == 200
    data2 = resp.json()
    assert len(data2) == 1

    # The two pages should return different invoices
    assert data[0]["id"] != data2[0]["id"]


# ══════════════════════════════════════════════════════════════════
# Credit Notes
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_and_list_credit_notes(client: AsyncClient, db):
    """Create a credit note from a validated invoice, then list credit notes."""
    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name, payment_terms_days)
        VALUES (:id, :tid, 'Credit Note Client', 30)
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    # Seed a validated invoice (credit notes require validated invoices)
    inv_id = str(uuid.uuid4())
    today = date.today()
    due = today + timedelta(days=30)
    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, invoice_number, status,
                              issue_date, due_date, total_ht, tva_rate, total_tva, total_ttc)
        VALUES (:id, :tid, :cid, 'FAC-TEST-001', 'validated', :idate, :ddate,
                500.0, 20.0, 100.0, 600.0)
    """), {"id": inv_id, "tid": TID, "cid": cust_id, "idate": today, "ddate": due})

    # Seed at least one invoice line (credit note copies lines)
    line_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO invoice_lines (id, invoice_id, description, quantity, unit_price, amount_ht, line_order)
        VALUES (:id, :inv_id, 'Test line', 1, 500.0, 500.0, 0)
    """), {"id": line_id, "inv_id": inv_id})
    await db.commit()

    # Create credit note
    resp = await client.post("/v1/billing/credit-notes", json={
        "invoice_id": inv_id,
        "notes": "Avoir de test",
    })
    assert resp.status_code == 201
    cn = resp.json()
    assert cn["invoice_id"] == inv_id
    assert cn["status"] == "draft"
    assert cn["total_ht"] == pytest.approx(-500.0, abs=0.01)
    assert cn["total_ttc"] == pytest.approx(-600.0, abs=0.01)

    # List credit notes
    resp = await client.get("/v1/billing/credit-notes")
    assert resp.status_code == 200
    cns = resp.json()
    assert len(cns) >= 1
    assert any(c["id"] == cn["id"] for c in cns)


# ══════════════════════════════════════════════════════════════════
# Supplier Invoices
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_supplier_invoices(client: AsyncClient, db):
    """Seed a supplier invoice via raw SQL, then verify it appears in the list."""
    si_id = str(uuid.uuid4())
    today = date.today()
    await db.execute(text("""
        INSERT INTO supplier_invoices (id, tenant_id, invoice_number, invoice_date,
                                       total_ht, total_tva, total_ttc, status)
        VALUES (:id, :tid, 'FOUR-001', :inv_date, 800.0, 160.0, 960.0, 'pending')
    """), {"id": si_id, "tid": TID, "inv_date": today})
    await db.commit()

    resp = await client.get("/v1/billing/supplier-invoices")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(si["id"] == si_id for si in data)
    found = next(si for si in data if si["id"] == si_id)
    assert found["invoice_number"] == "FOUR-001"
    assert found["status"] == "pending"


# ══════════════════════════════════════════════════════════════════
# Dunning Levels
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_dunning_level(client: AsyncClient):
    """POST /v1/billing/dunning/levels creates a level and returns 201."""
    resp = await client.post("/v1/billing/dunning/levels", json={
        "niveau": 1,
        "jours_apres_echeance": 30,
        "libelle": "Premier rappel",
    })
    assert resp.status_code == 201
    level = resp.json()
    assert level["niveau"] == 1
    assert level["jours_apres_echeance"] == 30
    assert level["libelle"] == "Premier rappel"
    assert level["is_active"] is True


@pytest.mark.asyncio
async def test_list_dunning_levels(client: AsyncClient):
    """After creating a level, it should appear in GET /v1/billing/dunning/levels."""
    # Create a level first
    resp = await client.post("/v1/billing/dunning/levels", json={
        "niveau": 2,
        "jours_apres_echeance": 60,
        "libelle": "Deuxieme rappel",
    })
    assert resp.status_code == 201
    created_id = resp.json()["id"]

    # List levels
    resp = await client.get("/v1/billing/dunning/levels")
    assert resp.status_code == 200
    levels = resp.json()
    assert len(levels) >= 1
    assert any(lv["id"] == created_id for lv in levels)


# ══════════════════════════════════════════════════════════════════
# Dunning — Overdue Invoices
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_overdue_invoices(client: AsyncClient, db):
    """Seed an overdue validated invoice, then check it appears in dunning/overdue."""
    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name, raison_sociale)
        VALUES (:id, :tid, 'Overdue Client', 'Overdue SARL')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    inv_id = str(uuid.uuid4())
    past_due = date.today() - timedelta(days=45)
    issue = past_due - timedelta(days=30)
    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, invoice_number, status,
                              issue_date, due_date, total_ht, tva_rate, total_tva, total_ttc)
        VALUES (:id, :tid, :cid, 'FAC-OVERDUE-001', 'validated', :idate, :ddate,
                1000.0, 20.0, 200.0, 1200.0)
    """), {"id": inv_id, "tid": TID, "cid": cust_id, "idate": issue, "ddate": past_due})
    await db.commit()

    resp = await client.get("/v1/billing/dunning/overdue")
    assert resp.status_code == 200
    overdue = resp.json()
    assert len(overdue) >= 1
    found = next((o for o in overdue if o["invoice_id"] == inv_id), None)
    assert found is not None
    assert found["invoice_number"] == "FAC-OVERDUE-001"
    assert found["days_overdue"] >= 45
    assert found["total_ttc"] == pytest.approx(1200.0, abs=0.01)


# ══════════════════════════════════════════════════════════════════
# Dunning — Actions
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_dunning_actions(client: AsyncClient, db):
    """Seed a dunning action via raw SQL, then verify it appears in GET dunning/actions."""
    cust_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name)
        VALUES (:id, :tid, 'Dunning Action Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    inv_id = str(uuid.uuid4())
    today = date.today()
    due = today - timedelta(days=10)
    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, invoice_number, status,
                              issue_date, due_date, total_ht, tva_rate, total_tva, total_ttc)
        VALUES (:id, :tid, :cid, 'FAC-DUN-001', 'validated', :idate, :ddate,
                500.0, 20.0, 100.0, 600.0)
    """), {"id": inv_id, "tid": TID, "cid": cust_id, "idate": today, "ddate": due})

    action_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO dunning_actions (id, tenant_id, invoice_id, customer_id,
                                     date_relance, mode, notes)
        VALUES (:id, :tid, :iid, :cid, :dr, 'EMAIL', 'Test relance')
    """), {"id": action_id, "tid": TID, "iid": inv_id, "cid": cust_id, "dr": today})
    await db.commit()

    resp = await client.get("/v1/billing/dunning/actions")
    assert resp.status_code == 200
    actions = resp.json()
    assert len(actions) >= 1
    found = next((a for a in actions if a["id"] == action_id), None)
    assert found is not None
    assert found["invoice_id"] == inv_id
    assert found["customer_id"] == cust_id
    assert found["mode"] == "EMAIL"
