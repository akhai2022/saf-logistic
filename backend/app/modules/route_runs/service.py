"""Route run regulation service.

Shared logic used by both the manual API endpoint and the daily Celery task.
Regulates overdue route runs that are stuck in DISPATCHED or IN_PROGRESS.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, time, timezone
from typing import Any

from sqlalchemy import text

logger = logging.getLogger(__name__)

REGULATABLE_STATUSES = ("DISPATCHED", "IN_PROGRESS")


def find_eligible_runs(
    db: Any,
    cutoff_date: date,
    *,
    tenant_id: str | None = None,
    run_ids: list[str] | None = None,
) -> list[Any]:
    """Find route runs eligible for regulation.

    Args:
        db: SQLAlchemy session (sync or async result proxy).
        cutoff_date: Runs with service_date < cutoff_date are eligible.
        tenant_id: Optional tenant filter (for manual regulation).
        run_ids: Optional explicit list of run IDs to check.

    Returns list of Row objects with run data.
    """
    q = """
        SELECT rr.id, rr.tenant_id, rr.code, rr.service_date, rr.status,
               rr.planned_start_at, rr.planned_end_at,
               rr.actual_start_at, rr.actual_end_at,
               rr.regulated_at
        FROM route_runs rr
        WHERE rr.service_date < :cutoff
          AND rr.status IN ('DISPATCHED', 'IN_PROGRESS')
          AND rr.regulated_at IS NULL
    """
    params: dict[str, Any] = {"cutoff": cutoff_date}

    if tenant_id:
        q += " AND rr.tenant_id = :tid"
        params["tid"] = tenant_id

    if run_ids:
        q += " AND rr.id = ANY(:ids)"
        params["ids"] = run_ids

    q += " ORDER BY rr.service_date ASC"
    return db.execute(text(q), params).fetchall()


def regulate_single_run(
    db: Any,
    run: Any,
    *,
    source: str,
    user_id: str | None = None,
    now: datetime | None = None,
) -> dict:
    """Regulate a single route run. Mutates DB but does NOT commit.

    Args:
        db: SQLAlchemy session.
        run: Row object from find_eligible_runs.
        source: 'manual' or 'automatic'.
        user_id: ID of the user who triggered regulation (None for automatic).
        now: Current timestamp (injectable for testing).

    Returns dict with regulation details for the run.
    """
    now = now or datetime.now(timezone.utc)
    run_id = str(run.id)
    old_status = run.status
    service_date = run.service_date

    # Determine actual_start_at
    actual_start = run.actual_start_at
    if actual_start is None:
        if run.planned_start_at:
            actual_start = run.planned_start_at
        else:
            # Default: service_date at 08:00 UTC
            actual_start = datetime.combine(service_date, time(8, 0), tzinfo=timezone.utc)

    # Determine actual_end_at
    actual_end = run.actual_end_at
    if actual_end is None:
        if run.planned_end_at:
            actual_end = run.planned_end_at
        else:
            # Default: service_date at 23:59 UTC
            actual_end = datetime.combine(service_date, time(23, 59), tzinfo=timezone.utc)

    # Aggregate financial totals from assigned missions
    totals = db.execute(
        text("""
            SELECT COALESCE(SUM(j.montant_vente_ht), 0) AS sale,
                   COALESCE(SUM(j.montant_achat_ht), 0) AS purchase
            FROM route_run_missions rrm
            JOIN jobs j ON rrm.mission_id = j.id
            WHERE rrm.route_run_id = :rid
        """),
        {"rid": run_id},
    ).first()

    sale = float(totals.sale) if totals else 0.0
    purchase = float(totals.purchase) if totals else 0.0
    margin = sale - purchase

    # Update the run
    db.execute(
        text("""
            UPDATE route_runs SET
                status = 'COMPLETED',
                actual_start_at = :start,
                actual_end_at = :end,
                aggregated_sale_amount_ht = :sale,
                aggregated_purchase_amount_ht = :purchase,
                aggregated_margin_ht = :margin,
                regulated_at = :now,
                regulated_by = :uid,
                regulation_source = :source,
                updated_at = :now
            WHERE id = :id
        """),
        {
            "id": run_id,
            "start": actual_start.isoformat() if isinstance(actual_start, datetime) else actual_start,
            "end": actual_end.isoformat() if isinstance(actual_end, datetime) else actual_end,
            "sale": sale,
            "purchase": purchase,
            "margin": margin,
            "now": now.isoformat(),
            "uid": user_id,
            "source": source,
        },
    )

    # Write audit log
    import json

    db.execute(
        text("""
            INSERT INTO audit_logs
                (id, tenant_id, user_id, action, entity_type,
                 entity_id, old_value, new_value, metadata)
            VALUES
                (:id, :tid, :uid, 'REGULATE', 'route_run',
                 :eid, CAST(:old AS json), CAST(:new AS json),
                 CAST(:meta AS json))
        """),
        {
            "id": str(uuid.uuid4()),
            "tid": str(run.tenant_id),
            "uid": user_id,
            "eid": run_id,
            "old": json.dumps({"status": old_status}),
            "new": json.dumps({
                "status": "COMPLETED",
                "aggregated_sale_amount_ht": sale,
                "aggregated_purchase_amount_ht": purchase,
                "aggregated_margin_ht": margin,
            }),
            "meta": json.dumps({
                "regulation_source": source,
                "service_date": service_date.isoformat(),
                "previous_actual_start_at": run.actual_start_at.isoformat() if run.actual_start_at else None,
                "previous_actual_end_at": run.actual_end_at.isoformat() if run.actual_end_at else None,
            }),
        },
    )

    return {
        "run_id": run_id,
        "code": run.code,
        "service_date": service_date.isoformat(),
        "old_status": old_status,
        "new_status": "COMPLETED",
        "aggregated_sale_amount_ht": sale,
        "aggregated_purchase_amount_ht": purchase,
        "aggregated_margin_ht": margin,
    }
