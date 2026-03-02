"""Celery tasks — run in sync context with their own DB sessions."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import date, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.infra.celery_app import celery_app

logger = logging.getLogger(__name__)


def _sync_url() -> str:
    return settings.DATABASE_URL.replace("+asyncpg", "+psycopg")


def _session() -> Session:
    engine = create_engine(_sync_url())
    return Session(engine)


# ---------------------------------------------------------------------------
# Compliance scan — progressive alerts, auto-expire, recalculate checklists
# ---------------------------------------------------------------------------
@celery_app.task(name="app.infra.tasks.compliance_scan_daily")
def compliance_scan_daily() -> dict:
    today = date.today()
    stats = {"expired": 0, "alerts_created": 0, "checklists_updated": 0}

    with _session() as db:
        # 1. Auto-transition VALIDE → EXPIRE when date_expiration < today
        expired_rows = db.execute(
            text("""
                UPDATE documents
                SET statut = 'EXPIRE',
                    compliance_status = 'expired',
                    updated_at = NOW()
                WHERE date_expiration IS NOT NULL
                  AND date_expiration < :today
                  AND COALESCE(statut, 'VALIDE') = 'VALIDE'
                RETURNING id, tenant_id, entity_type, entity_id,
                          type_document, doc_type, date_expiration
            """),
            {"today": today},
        ).fetchall()
        stats["expired"] = len(expired_rows)

        # 2. Generate progressive alerts (J-60, J-30, J-15, J-7, J0)
        alert_thresholds = [
            (60, "EXPIRATION_J60", "alerte_j60_envoyee"),
            (30, "EXPIRATION_J30", "alerte_j30_envoyee"),
            (15, "EXPIRATION_J15", "alerte_j15_envoyee"),
            (7, "EXPIRATION_J7", "alerte_j7_envoyee"),
            (0, "EXPIRATION_J0", "alerte_j0_envoyee"),
        ]

        for days_before, alert_type, flag_col in alert_thresholds:
            threshold_date = today + timedelta(days=days_before)

            # Find documents expiring at this threshold that haven't been alerted
            docs = db.execute(
                text(f"""
                    SELECT id, tenant_id, entity_type, entity_id,
                           date_expiration, is_critical
                    FROM documents
                    WHERE date_expiration IS NOT NULL
                      AND date_expiration <= :threshold
                      AND COALESCE(statut, 'VALIDE') IN ('VALIDE', 'EXPIRE')
                      AND COALESCE({flag_col}, false) = false
                """),
                {"threshold": threshold_date},
            ).fetchall()

            for doc in docs:
                # Create alert
                db.execute(
                    text("""
                        INSERT INTO compliance_alerts (
                            id, tenant_id, document_id, entity_type, entity_id,
                            type_alerte, date_expiration_document,
                            statut, canaux_utilises
                        ) VALUES (
                            :id, :tid, :did, :etype, :eid,
                            :atype, :dexp,
                            'ENVOYEE', '{IN_APP,EMAIL}'
                        )
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "tid": str(doc.tenant_id),
                        "did": str(doc.id),
                        "etype": doc.entity_type,
                        "eid": str(doc.entity_id),
                        "atype": alert_type,
                        "dexp": doc.date_expiration,
                    },
                )

                # Mark flag so we don't send again
                db.execute(
                    text(f"""
                        UPDATE documents SET {flag_col} = true, updated_at = NOW()
                        WHERE id = :id
                    """),
                    {"id": str(doc.id)},
                )
                stats["alerts_created"] += 1

        # Also create legacy tasks for backward compat
        for doc in expired_rows:
            db.execute(
                text("""
                    INSERT INTO tasks (id, tenant_id, category, title,
                                       entity_type, entity_id, due_date,
                                       status, created_at)
                    VALUES (:id, :tid, 'compliance', :title,
                            :etype, :eid, :due, 'open', NOW())
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": str(uuid.uuid4()),
                    "tid": str(doc.tenant_id),
                    "title": f"Document {doc.type_document or doc.doc_type} expired {doc.date_expiration}",
                    "etype": doc.entity_type,
                    "eid": str(doc.entity_id),
                    "due": doc.date_expiration,
                },
            )

        # 3. Recalculate compliance_checklists for affected entities
        affected_entities = set()
        for doc in expired_rows:
            affected_entities.add((str(doc.tenant_id), doc.entity_type, str(doc.entity_id)))

        # Also include entities from newly-created alerts
        alert_entities = db.execute(
            text("""
                SELECT DISTINCT tenant_id, entity_type, entity_id
                FROM compliance_alerts
                WHERE created_at >= :today_start
            """),
            {"today_start": f"{today}T00:00:00"},
        ).fetchall()
        for ae in alert_entities:
            affected_entities.add((str(ae.tenant_id), ae.entity_type, str(ae.entity_id)))

        for tid, etype, eid in affected_entities:
            _recalculate_compliance_sync(db, tid, etype, eid, today)
            stats["checklists_updated"] += 1

        db.commit()

    return stats


def _recalculate_compliance_sync(
    db: Session, tenant_id: str, entity_type: str, entity_id: str, today: date
) -> None:
    """Sync version of compliance recalculation for Celery tasks."""
    templates = db.execute(text("""
        SELECT * FROM compliance_templates
        WHERE tenant_id = :tid AND entity_type = :etype AND is_active = true
        ORDER BY ordre_affichage
    """), {"tid": tenant_id, "etype": entity_type}).fetchall()

    nb_requis = 0
    nb_valides = 0
    nb_manquants = 0
    nb_expires = 0
    nb_expirant = 0
    has_bloquant = False
    items = []

    for tpl in templates:
        nb_requis += 1
        doc = db.execute(text("""
            SELECT id, date_expiration, statut FROM documents
            WHERE tenant_id = :tid AND entity_type = :etype AND entity_id = :eid
              AND (type_document = :dtype OR doc_type = :dtype)
              AND COALESCE(statut, 'VALIDE') NOT IN ('ARCHIVE', 'REJETE', 'BROUILLON')
            ORDER BY version DESC, created_at DESC LIMIT 1
        """), {
            "tid": tenant_id, "etype": entity_type,
            "eid": entity_id, "dtype": tpl.type_document,
        }).first()

        if not doc:
            nb_manquants += 1
            if tpl.bloquant:
                has_bloquant = True
            items.append({"type_document": tpl.type_document, "statut": "MANQUANT"})
            continue

        exp = doc.date_expiration
        doc_statut = doc.statut or "VALIDE"

        if doc_statut == "EXPIRE" or (exp and exp < today):
            nb_expires += 1
            if tpl.bloquant:
                has_bloquant = True
            items.append({"type_document": tpl.type_document, "statut": "EXPIRE"})
        elif exp and (exp - today).days <= 60:
            nb_expirant += 1
            nb_valides += 1
            items.append({"type_document": tpl.type_document, "statut": "EXPIRANT"})
        else:
            nb_valides += 1
            items.append({"type_document": tpl.type_document, "statut": "OK"})

    if has_bloquant:
        statut_global = "BLOQUANT"
    elif nb_manquants > 0 or nb_expires > 0 or nb_expirant > 0:
        statut_global = "A_REGULARISER"
    else:
        statut_global = "OK"

    taux = round((nb_valides / nb_requis * 100), 2) if nb_requis > 0 else 100.0

    db.execute(text("""
        INSERT INTO compliance_checklists (
            id, tenant_id, entity_type, entity_id, statut_global,
            nb_documents_requis, nb_documents_valides, nb_documents_manquants,
            nb_documents_expires, nb_documents_expirant_bientot,
            taux_conformite_pourcent, details, derniere_mise_a_jour
        ) VALUES (
            gen_random_uuid(), :tid, :etype, :eid, :sg,
            :req, :val, :man, :exp, :expb,
            :taux, :det, NOW()
        )
        ON CONFLICT (tenant_id, entity_type, entity_id)
        DO UPDATE SET
            statut_global = :sg,
            nb_documents_requis = :req, nb_documents_valides = :val,
            nb_documents_manquants = :man, nb_documents_expires = :exp,
            nb_documents_expirant_bientot = :expb,
            taux_conformite_pourcent = :taux, details = :det,
            derniere_mise_a_jour = NOW(), updated_at = NOW()
    """), {
        "tid": tenant_id, "etype": entity_type, "eid": entity_id,
        "sg": statut_global, "req": nb_requis, "val": nb_valides,
        "man": nb_manquants, "exp": nb_expires, "expb": nb_expirant,
        "taux": taux, "det": json.dumps(items),
    })

    # Update entity conformite_statut
    entity_table = {
        "DRIVER": "drivers", "VEHICLE": "vehicles",
        "SUBCONTRACTOR": "subcontractors",
    }.get(entity_type)
    if entity_table:
        db.execute(text(f"""
            UPDATE {entity_table} SET conformite_statut = :sg
            WHERE id = :eid AND tenant_id = :tid
        """), {"sg": statut_global, "eid": entity_id, "tid": tenant_id})


# ---------------------------------------------------------------------------
# Invoice due-date reminders
# ---------------------------------------------------------------------------
@celery_app.task(name="app.infra.tasks.send_due_reminders_daily")
def send_due_reminders_daily() -> dict:
    today = date.today()
    remind_date = today + timedelta(days=7)
    with _session() as db:
        rows = db.execute(
            text("""
                SELECT id, tenant_id, invoice_number, due_date, customer_id
                FROM invoices
                WHERE status = 'validated'
                  AND due_date BETWEEN :today AND :remind
                  AND id NOT IN (SELECT entity_id::uuid FROM tasks WHERE category = 'billing_reminder')
            """),
            {"today": today, "remind": remind_date},
        )
        invoices = rows.fetchall()
        for inv in invoices:
            db.execute(
                text("""
                    INSERT INTO tasks (id, tenant_id, category, title, entity_type, entity_id, due_date, status, created_at)
                    VALUES (:id, :tid, 'billing_reminder', :title, 'invoice', :eid, :due, 'open', NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "tid": str(inv.tenant_id),
                    "title": f"Invoice {inv.invoice_number} due {inv.due_date}",
                    "eid": str(inv.id),
                    "due": inv.due_date,
                },
            )
        db.commit()
    return {"reminders_created": len(invoices)}


# ---------------------------------------------------------------------------
# OCR processing
# ---------------------------------------------------------------------------
@celery_app.task(name="app.infra.tasks.ocr_process_job", queue="ocr")
def ocr_process_job(ocr_job_id: str) -> dict:
    from app.modules.ocr.providers.base import OcrResult

    with _session() as db:
        row = db.execute(
            text("SELECT * FROM ocr_jobs WHERE id = :id"),
            {"id": ocr_job_id},
        ).first()
        if not row:
            return {"error": "OCR job not found"}

        db.execute(
            text("UPDATE ocr_jobs SET status = 'processing', started_at = NOW() WHERE id = :id"),
            {"id": ocr_job_id},
        )
        db.commit()

        provider_name = settings.OCR_PROVIDER
        result: OcrResult

        if provider_name == "MOCK":
            result = OcrResult(
                supplier_name="Fournisseur Test",
                invoice_number="MOCK-001",
                invoice_date="2024-01-15",
                total_ht=1000.00,
                total_ttc=1200.00,
                tva=200.00,
                confidence=0.95,
                raw_text="Mock OCR text",
                line_items=[],
            )
        elif provider_name == "OPEN_SOURCE":
            from app.modules.ocr.providers.paddle_provider import PaddleOcrProvider
            from app.infra.s3 import _get_s3_client
            import tempfile
            import os

            s3 = _get_s3_client()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                s3.download_fileobj(settings.S3_BUCKET, row.s3_key, tmp)
                tmp_path = tmp.name

            try:
                provider = PaddleOcrProvider()
                result = provider.extract(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            result = OcrResult(
                supplier_name=None, invoice_number=None, invoice_date=None,
                total_ht=None, total_ttc=None, tva=None,
                confidence=0.0, raw_text="Unknown provider", line_items=[],
            )

        db.execute(
            text("""
                UPDATE ocr_jobs SET
                    status = 'needs_review',
                    finished_at = NOW(),
                    extracted_data = :data,
                    confidence = :conf
                WHERE id = :id
            """),
            {
                "id": ocr_job_id,
                "data": json.dumps({
                    "supplier_name": result.supplier_name,
                    "invoice_number": result.invoice_number,
                    "invoice_date": result.invoice_date,
                    "total_ht": result.total_ht,
                    "total_ttc": result.total_ttc,
                    "tva": result.tva,
                    "raw_text": result.raw_text,
                    "line_items": result.line_items,
                }),
                "conf": result.confidence,
            },
        )
        db.commit()

    return {"status": "needs_review", "confidence": result.confidence}


# ---------------------------------------------------------------------------
# Invoice PDF generation
# ---------------------------------------------------------------------------
@celery_app.task(name="app.infra.tasks.invoice_generate_pdf")
def invoice_generate_pdf(invoice_id: str) -> dict:
    with _session() as db:
        inv = db.execute(
            text("SELECT * FROM invoices WHERE id = :id"), {"id": invoice_id}
        ).first()
        if not inv:
            return {"error": "Invoice not found"}

        lines = db.execute(
            text("SELECT * FROM invoice_lines WHERE invoice_id = :id ORDER BY line_order"),
            {"id": invoice_id},
        ).fetchall()

        customer = db.execute(
            text("SELECT * FROM customers WHERE id = :id"), {"id": str(inv.customer_id)}
        ).first()

        tenant = db.execute(
            text("SELECT * FROM tenants WHERE id = :id"), {"id": str(inv.tenant_id)}
        ).first()

    from app.modules.billing.pdf_service import generate_invoice_pdf
    pdf_bytes = generate_invoice_pdf(inv, lines, customer, tenant)

    # Upload to S3
    from app.infra.s3 import _get_s3_client
    s3 = _get_s3_client()
    key = f"{inv.tenant_id}/invoices/{inv.invoice_number}.pdf"
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=pdf_bytes, ContentType="application/pdf")

    with _session() as db:
        db.execute(
            text("UPDATE invoices SET pdf_s3_key = :key WHERE id = :id"),
            {"key": key, "id": invoice_id},
        )
        db.commit()

    return {"pdf_key": key}


# ---------------------------------------------------------------------------
# Driver auto-inactivation — daily
# ---------------------------------------------------------------------------
@celery_app.task(name="app.infra.tasks.driver_auto_inactivation")
def driver_auto_inactivation() -> dict:
    """Daily: set drivers with date_sortie < today to INACTIF."""
    today = date.today()
    with _session() as db:
        result = db.execute(
            text("""
                UPDATE drivers
                SET statut = 'INACTIF', is_active = false, updated_at = NOW()
                WHERE date_sortie IS NOT NULL
                  AND date_sortie < :today
                  AND statut = 'ACTIF'
                RETURNING id, tenant_id
            """),
            {"today": today},
        )
        rows = result.fetchall()
        db.commit()
    return {"inactivated": len(rows)}


# ---------------------------------------------------------------------------
# Notification dispatch
# ---------------------------------------------------------------------------
@celery_app.task(name="app.infra.tasks.notification_dispatch")
def notification_dispatch(
    tenant_id: str,
    event_type: str,
    title: str,
    message: str | None = None,
    link: str | None = None,
) -> dict:
    """Look up notification_configs, find matching users by role, INSERT notifications."""
    with _session() as db:
        # Find active config for this event
        configs = db.execute(
            text("""
                SELECT channels, recipients FROM notification_configs
                WHERE tenant_id = :tid AND event_type = :evt AND is_active = true
            """),
            {"tid": tenant_id, "evt": event_type},
        ).fetchall()

        if not configs:
            return {"dispatched": 0}

        # Collect all target role names
        target_roles: set[str] = set()
        for cfg in configs:
            if cfg.recipients:
                target_roles.update(cfg.recipients)

        # If no specific recipients, send to all admin users
        if not target_roles:
            target_roles = {"admin"}

        # Find user IDs by role name
        users = db.execute(
            text("""
                SELECT u.id FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.tenant_id = :tid AND u.is_active = true
                  AND r.name = ANY(:roles)
            """),
            {"tid": tenant_id, "roles": list(target_roles)},
        ).fetchall()

        count = 0
        for u in users:
            db.execute(
                text("""
                    INSERT INTO notifications (id, tenant_id, user_id, title, message, link, event_type)
                    VALUES (:id, :tid, :uid, :title, :msg, :link, :evt)
                """),
                {
                    "id": str(uuid.uuid4()), "tid": tenant_id,
                    "uid": str(u.id), "title": title,
                    "msg": message, "link": link, "evt": event_type,
                },
            )
            count += 1

        db.commit()

    return {"dispatched": count}


# ---------------------------------------------------------------------------
# Credit note PDF generation
# ---------------------------------------------------------------------------
@celery_app.task(name="app.infra.tasks.credit_note_generate_pdf")
def credit_note_generate_pdf(credit_note_id: str) -> dict:
    with _session() as db:
        cn = db.execute(
            text("SELECT * FROM credit_notes WHERE id = :id"), {"id": credit_note_id}
        ).first()
        if not cn:
            return {"error": "Credit note not found"}

        lines = db.execute(
            text("SELECT * FROM credit_note_lines WHERE credit_note_id = :id ORDER BY line_order"),
            {"id": credit_note_id},
        ).fetchall()

        customer = db.execute(
            text("SELECT * FROM customers WHERE id = :id"), {"id": str(cn.customer_id)}
        ).first()

        tenant = db.execute(
            text("SELECT * FROM tenants WHERE id = :id"), {"id": str(cn.tenant_id)}
        ).first()

    from app.modules.billing.pdf_service import generate_credit_note_pdf
    pdf_bytes = generate_credit_note_pdf(cn, lines, customer, tenant)

    # Upload to S3
    from app.infra.s3 import _get_s3_client
    s3 = _get_s3_client()
    key = f"{cn.tenant_id}/credit-notes/{cn.credit_note_number}.pdf"
    s3.put_object(Bucket=settings.S3_BUCKET, Key=key, Body=pdf_bytes, ContentType="application/pdf")

    with _session() as db:
        db.execute(
            text("UPDATE credit_notes SET pdf_s3_key = :key WHERE id = :id"),
            {"key": key, "id": credit_note_id},
        )
        db.commit()

    return {"pdf_key": key}
