"""Integration tests: Celery task functions called directly (no broker)."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text

TID = "00000000-0000-0000-0000-000000000001"
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000100"


@pytest_asyncio.fixture(autouse=True)
async def clean_task_data(db):
    """Clean up data touched by Celery tasks before each test."""
    await db.execute(text("DELETE FROM compliance_alerts WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM compliance_checklists WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM documents WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM compliance_templates WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM notifications WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM notification_configs WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM tasks WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dunning_actions WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text("DELETE FROM dunning_levels WHERE tenant_id = :tid"), {"tid": TID})
    await db.execute(text(
        "DELETE FROM invoice_lines WHERE invoice_id IN (SELECT id FROM invoices WHERE tenant_id = :tid)"
    ), {"tid": TID})
    await db.execute(text("DELETE FROM invoices WHERE tenant_id = :tid"), {"tid": TID})
    # Clean test drivers that we seed (avoid removing seed data from conftest)
    await db.execute(text(
        "DELETE FROM drivers WHERE tenant_id = :tid AND matricule LIKE 'CELERY-%'"
    ), {"tid": TID})
    await db.commit()
    yield


# ══════════════════════════════════════════════════════════════════
# 1. Driver auto-inactivation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_driver_auto_inactivation(db):
    """Seed a driver with date_sortie in the past + statut ACTIF, call task, verify INACTIF."""
    driver_id = str(uuid.uuid4())
    mat = f"CELERY-{uuid.uuid4().hex[:6]}"
    yesterday = date.today() - timedelta(days=1)

    await db.execute(text("""
        INSERT INTO drivers (id, tenant_id, first_name, last_name, matricule, nom, prenom,
                             statut, is_active, date_sortie)
        VALUES (:id, :tid, 'Inactive', 'Driver', :mat, 'Driver', 'Inactive',
                'ACTIF', true, :sortie)
        ON CONFLICT (id) DO NOTHING
    """), {"id": driver_id, "tid": TID, "mat": mat, "sortie": yesterday})
    await db.commit()

    # Call the task function directly (sync)
    from app.infra.tasks import driver_auto_inactivation
    result = driver_auto_inactivation()
    assert result["inactivated"] >= 1

    # Verify via async session
    row = (await db.execute(
        text("SELECT statut, is_active FROM drivers WHERE id = :id"),
        {"id": driver_id},
    )).first()
    assert row.statut == "INACTIF"
    assert row.is_active is False


# ══════════════════════════════════════════════════════════════════
# 2. Compliance scan — expire documents
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_compliance_scan_expires_documents(db):
    """Seed a VALIDE document with past expiration, call compliance_scan_daily, verify EXPIRE."""
    driver_id = str(uuid.uuid4())
    mat = f"CELERY-{uuid.uuid4().hex[:6]}"
    doc_id = str(uuid.uuid4())
    expired_date = date.today() - timedelta(days=10)

    # Seed driver
    await db.execute(text("""
        INSERT INTO drivers (id, tenant_id, first_name, last_name, matricule, nom, prenom, statut)
        VALUES (:id, :tid, 'Comp', 'Driver', :mat, 'Driver', 'Comp', 'ACTIF')
        ON CONFLICT (id) DO NOTHING
    """), {"id": driver_id, "tid": TID, "mat": mat})

    # Seed document with expired date but status VALIDE
    await db.execute(text("""
        INSERT INTO documents (id, tenant_id, entity_type, entity_id, doc_type,
                               statut, compliance_status, date_expiration, s3_key)
        VALUES (:id, :tid, 'DRIVER', :eid, 'PERMIS_CONDUIRE',
                'VALIDE', 'valid', :exp, 'test/permis.pdf')
        ON CONFLICT DO NOTHING
    """), {"id": doc_id, "tid": TID, "eid": driver_id, "exp": expired_date})
    await db.commit()

    # Call the task function directly
    from app.infra.tasks import compliance_scan_daily
    result = compliance_scan_daily()
    assert result["expired"] >= 1

    # Verify document is now EXPIRE
    row = (await db.execute(
        text("SELECT statut, compliance_status FROM documents WHERE id = :id"),
        {"id": doc_id},
    )).first()
    assert row.statut == "EXPIRE"
    assert row.compliance_status == "expired"


# ══════════════════════════════════════════════════════════════════
# 3. Notification dispatch
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_notification_dispatch(db):
    """Seed notification_config, call notification_dispatch, verify notification row."""
    config_id = str(uuid.uuid4())

    # Seed a notification config for a TEST_EVENT targeting 'admin' role
    await db.execute(text("""
        INSERT INTO notification_configs (id, tenant_id, event_type, recipients, is_active, channels)
        VALUES (:id, :tid, 'TEST_EVENT', '{admin}', true, '{IN_APP}')
        ON CONFLICT DO NOTHING
    """), {"id": config_id, "tid": TID})
    await db.commit()

    # Call the task function directly
    from app.infra.tasks import notification_dispatch
    result = notification_dispatch(TID, "TEST_EVENT", "Test Title", "Test message")
    assert result["dispatched"] >= 1

    # Verify a notification row was created for the admin user
    row = (await db.execute(text("""
        SELECT title, message, event_type, user_id FROM notifications
        WHERE tenant_id = :tid AND event_type = 'TEST_EVENT'
        ORDER BY created_at DESC LIMIT 1
    """), {"tid": TID})).first()
    assert row is not None
    assert row.title == "Test Title"
    assert row.message == "Test message"
    assert row.event_type == "TEST_EVENT"
    assert str(row.user_id) == ADMIN_USER_ID


# ══════════════════════════════════════════════════════════════════
# 4. Dunning check — create actions for overdue invoices
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dunning_check_creates_actions(db):
    """Seed dunning_level + overdue invoice, call dunning_check_daily, verify action created."""
    cust_id = str(uuid.uuid4())
    inv_id = str(uuid.uuid4())
    level_id = str(uuid.uuid4())
    due_date = date.today() - timedelta(days=30)

    # Seed customer
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name)
        VALUES (:id, :tid, 'Dunning Test Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    # Seed overdue invoice (status='validated', due_date 30 days ago)
    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, invoice_number, status,
                              due_date, total_ht, total_tva, total_ttc, tva_rate)
        VALUES (:id, :tid, :cid, 'DUNN-001', 'validated',
                :due, 1000.00, 200.00, 1200.00, 20.0)
        ON CONFLICT DO NOTHING
    """), {"id": inv_id, "tid": TID, "cid": cust_id, "due": due_date})

    # Seed dunning level (niveau 1, triggers at 15 days overdue)
    await db.execute(text("""
        INSERT INTO dunning_levels (id, tenant_id, niveau, libelle, jours_apres_echeance, is_active)
        VALUES (:id, :tid, 1, 'Relance niveau 1', 15, true)
        ON CONFLICT DO NOTHING
    """), {"id": level_id, "tid": TID})
    await db.commit()

    # Call the task function directly
    from app.infra.tasks import dunning_check_daily
    result = dunning_check_daily()
    assert result["actions_created"] >= 1

    # Verify a dunning_action was created
    action = (await db.execute(text("""
        SELECT invoice_id, dunning_level_id, mode FROM dunning_actions
        WHERE tenant_id = :tid AND invoice_id = :iid
        LIMIT 1
    """), {"tid": TID, "iid": inv_id})).first()
    assert action is not None
    assert str(action.invoice_id) == inv_id
    assert str(action.dunning_level_id) == level_id
    assert action.mode == "EMAIL"


# ══════════════════════════════════════════════════════════════════
# 5. Send due reminders — create tasks for invoices due soon
# ══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_send_due_reminders(db):
    """Seed an invoice due in 5 days, call send_due_reminders_daily, verify task created."""
    cust_id = str(uuid.uuid4())
    inv_id = str(uuid.uuid4())
    due_in_5 = date.today() + timedelta(days=5)

    # Seed customer
    await db.execute(text("""
        INSERT INTO customers (id, tenant_id, name)
        VALUES (:id, :tid, 'Reminder Test Client')
        ON CONFLICT (id) DO NOTHING
    """), {"id": cust_id, "tid": TID})

    # Seed invoice due in 5 days (within the 7-day reminder window)
    await db.execute(text("""
        INSERT INTO invoices (id, tenant_id, customer_id, invoice_number, status,
                              due_date, total_ht, total_tva, total_ttc, tva_rate)
        VALUES (:id, :tid, :cid, 'REM-001', 'validated',
                :due, 500.00, 100.00, 600.00, 20.0)
        ON CONFLICT DO NOTHING
    """), {"id": inv_id, "tid": TID, "cid": cust_id, "due": due_in_5})
    await db.commit()

    # Call the task function directly
    from app.infra.tasks import send_due_reminders_daily
    result = send_due_reminders_daily()
    assert result["reminders_created"] >= 1

    # Verify a task row was created for this invoice
    task_row = (await db.execute(text("""
        SELECT title, category, entity_type, entity_id, status FROM tasks
        WHERE tenant_id = :tid AND category = 'billing_reminder' AND entity_id = :eid
        LIMIT 1
    """), {"tid": TID, "eid": str(inv_id)})).first()
    assert task_row is not None
    assert task_row.category == "billing_reminder"
    assert task_row.entity_type == "invoice"
    assert task_row.status == "open"
    assert "REM-001" in task_row.title
