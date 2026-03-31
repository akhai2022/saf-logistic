"""Integration tests for route_runs module — CRUD, transitions, and regulation."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.tests.conftest import ADMIN_ID, TENANT_ID, TENANT_B_ID

pytestmark = pytest.mark.asyncio


# ── Helpers ───────────────────────────────────────────────────────

async def _create_run(
    client: AsyncClient,
    service_date: str,
    *,
    notes: str | None = None,
) -> dict:
    resp = await client.post("/v1/route-runs", json={
        "service_date": service_date,
        "notes": notes,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _seed_job(db: AsyncSession, tenant_id: str, *, sale: float = 100, purchase: float = 60) -> str:
    """Insert a minimal job and return its ID."""
    job_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO jobs (id, tenant_id, numero, status, montant_vente_ht, montant_achat_ht)
        VALUES (:id, :tid, :num, 'CONFIRMED', :sale, :purchase)
    """), {"id": job_id, "tid": tenant_id, "num": f"J-{uuid.uuid4().hex[:6]}", "sale": sale, "purchase": purchase})
    await db.commit()
    return job_id


async def _transition(client: AsyncClient, run_id: str, endpoint: str) -> dict:
    resp = await client.post(f"/v1/route-runs/{run_id}/{endpoint}")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── CRUD tests ────────────────────────────────────────────────────

class TestRouteRunCRUD:

    async def test_create_and_list(self, client: AsyncClient, seed_db):
        run = await _create_run(client, date.today().isoformat())
        assert run["status"] == "PLANNED"
        assert run["code"].startswith("RUN-")

        resp = await client.get("/v1/route-runs", params={
            "date_from": date.today().isoformat(),
            "date_to": date.today().isoformat(),
        })
        assert resp.status_code == 200
        codes = [r["code"] for r in resp.json()]
        assert run["code"] in codes

    async def test_get_detail(self, client: AsyncClient, seed_db):
        run = await _create_run(client, date.today().isoformat())
        resp = await client.get(f"/v1/route-runs/{run['id']}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["code"] == run["code"]
        assert detail["missions"] == []


# ── Transition tests ──────────────────────────────────────────────

class TestRouteRunTransitions:

    async def test_full_lifecycle(self, client: AsyncClient, seed_db):
        run = await _create_run(client, date.today().isoformat())
        assert run["status"] == "PLANNED"

        r = await _transition(client, run["id"], "dispatch")
        assert r["status"] == "DISPATCHED"

        r = await _transition(client, run["id"], "start")
        assert r["status"] == "IN_PROGRESS"

        r = await _transition(client, run["id"], "complete")
        assert r["status"] == "COMPLETED"

    async def test_invalid_transition_rejected(self, client: AsyncClient, seed_db):
        run = await _create_run(client, date.today().isoformat())
        resp = await client.post(f"/v1/route-runs/{run['id']}/complete")
        assert resp.status_code == 422

    async def test_cancel_from_dispatched(self, client: AsyncClient, seed_db):
        run = await _create_run(client, date.today().isoformat())
        await _transition(client, run["id"], "dispatch")
        r = await _transition(client, run["id"], "cancel")
        assert r["status"] == "CANCELLED"


# ── Regulation tests ──────────────────────────────────────────────

class TestRegulation:

    async def _setup_overdue_run(
        self, client: AsyncClient, db: AsyncSession, *, status: str = "DISPATCHED", days_ago: int = 2,
    ) -> str:
        """Create a run with a past service_date and advance it to the given status."""
        past_date = (date.today() - timedelta(days=days_ago)).isoformat()
        run = await _create_run(client, past_date)
        run_id = run["id"]

        await _transition(client, run_id, "dispatch")
        if status == "IN_PROGRESS":
            await _transition(client, run_id, "start")

        return run_id

    async def test_preview_returns_eligible_without_mutating(self, client: AsyncClient, db: AsyncSession, seed_db):
        run_id = await self._setup_overdue_run(client, db, status="DISPATCHED")

        resp = await client.post("/v1/route-runs/regulate", json={"preview": True})
        assert resp.status_code == 200
        body = resp.json()
        assert body["eligible"] >= 1
        assert body["regulated"] == 0

        # Verify run is still DISPATCHED
        detail = (await client.get(f"/v1/route-runs/{run_id}")).json()
        assert detail["status"] == "DISPATCHED"

    async def test_regulate_dispatched_run(self, client: AsyncClient, db: AsyncSession, seed_db):
        run_id = await self._setup_overdue_run(client, db, status="DISPATCHED")

        resp = await client.post("/v1/route-runs/regulate", json={"run_ids": [run_id]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["regulated"] >= 1
        assert body["errors"] == 0

        detail = (await client.get(f"/v1/route-runs/{run_id}")).json()
        assert detail["status"] == "COMPLETED"
        assert detail["regulated_at"] is not None
        assert detail["regulation_source"] == "manual"
        assert detail["actual_start_at"] is not None
        assert detail["actual_end_at"] is not None

    async def test_regulate_in_progress_run(self, client: AsyncClient, db: AsyncSession, seed_db):
        run_id = await self._setup_overdue_run(client, db, status="IN_PROGRESS")

        resp = await client.post("/v1/route-runs/regulate", json={"run_ids": [run_id]})
        assert resp.status_code == 200
        body = resp.json()
        assert body["regulated"] >= 1

        detail = (await client.get(f"/v1/route-runs/{run_id}")).json()
        assert detail["status"] == "COMPLETED"
        assert detail["actual_start_at"] is not None  # Should be preserved from start transition

    async def test_regulate_computes_aggregates(self, client: AsyncClient, db: AsyncSession, seed_db):
        run_id = await self._setup_overdue_run(client, db, status="DISPATCHED")

        # Assign a job with known amounts
        job_id = await _seed_job(db, str(TENANT_ID), sale=500.0, purchase=200.0)
        resp = await client.post(f"/v1/route-runs/{run_id}/assign-mission", json={"mission_id": job_id})
        assert resp.status_code == 200

        # Regulate
        resp = await client.post("/v1/route-runs/regulate", json={"run_ids": [run_id]})
        assert resp.status_code == 200

        detail = (await client.get(f"/v1/route-runs/{run_id}")).json()
        assert float(detail["aggregated_sale_amount_ht"]) == 500.0
        assert float(detail["aggregated_purchase_amount_ht"]) == 200.0
        assert float(detail["aggregated_margin_ht"]) == 300.0

    async def test_idempotency_prevents_double_regulation(self, client: AsyncClient, db: AsyncSession, seed_db):
        run_id = await self._setup_overdue_run(client, db, status="DISPATCHED")

        # First regulation
        resp = await client.post("/v1/route-runs/regulate", json={"run_ids": [run_id]})
        assert resp.json()["regulated"] >= 1

        # Second attempt — should find 0 eligible
        resp = await client.post("/v1/route-runs/regulate", json={"run_ids": [run_id]})
        body = resp.json()
        assert body["eligible"] == 0
        assert body["regulated"] == 0

    async def test_today_runs_not_eligible(self, client: AsyncClient, seed_db):
        """Runs with service_date = today should NOT be eligible for regulation."""
        run = await _create_run(client, date.today().isoformat())
        await _transition(client, run["id"], "dispatch")

        resp = await client.post("/v1/route-runs/regulate", json={
            "run_ids": [run["id"]],
            "preview": True,
        })
        assert resp.json()["eligible"] == 0

    async def test_regulation_writes_audit_log(self, client: AsyncClient, db: AsyncSession, seed_db):
        run_id = await self._setup_overdue_run(client, db, status="DISPATCHED")

        await client.post("/v1/route-runs/regulate", json={"run_ids": [run_id]})

        row = (await db.execute(text("""
            SELECT action, entity_type, entity_id, metadata
            FROM audit_logs
            WHERE entity_id = :eid AND action = 'REGULATE'
            ORDER BY created_at DESC LIMIT 1
        """), {"eid": run_id})).first()

        assert row is not None
        assert row.action == "REGULATE"
        assert row.entity_type == "route_run"

    async def test_tenant_isolation(self, client: AsyncClient, client_tenant_b: AsyncClient, db: AsyncSession, seed_db, seed_tenant_b):
        """Tenant A regulation must not see Tenant B runs."""
        # Create overdue run in Tenant A
        run_a = await self._setup_overdue_run(client, db, status="DISPATCHED")

        # Create overdue run in Tenant B
        past_date = (date.today() - timedelta(days=2)).isoformat()
        run_b_resp = await client_tenant_b.post("/v1/route-runs", json={"service_date": past_date})
        assert run_b_resp.status_code == 201
        run_b_id = run_b_resp.json()["id"]
        await client_tenant_b.post(f"/v1/route-runs/{run_b_id}/dispatch")

        # Regulate from Tenant A — should only see Tenant A runs
        resp = await client.post("/v1/route-runs/regulate", json={"preview": True})
        eligible_ids = [d["run_id"] for d in resp.json()["details"]]
        assert run_a in eligible_ids
        assert run_b_id not in eligible_ids
