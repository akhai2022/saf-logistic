"""Fix data issues:
1. Tournée 1406 uses AW-639-SE which is already used by 1017 → assign DF-314-VL instead
2. Advance missions to realistic statuses (past dates → CLOTUREE, recent → LIVREE/EN_COURS)
"""
from __future__ import annotations

import asyncio
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory

TENANT_ID = "10000000-0000-0000-0000-000000000001"


async def fix(db: AsyncSession) -> None:
    tid = TENANT_ID
    today = date.today()

    # ── 1. Fix duplicate vehicle AW-639-SE ────────────────────────
    print("Fixing duplicate vehicle assignment...")
    # Find DF-314-VL ID
    veh = (await db.execute(text(
        "SELECT id FROM vehicles WHERE tenant_id = :tid AND immatriculation = 'DF-314-VL'"
    ), {"tid": tid})).first()
    if veh:
        new_vid = str(veh.id)
        # Update template 1406
        await db.execute(text("""
            UPDATE route_templates SET default_vehicle_id = :vid, updated_at = NOW()
            WHERE tenant_id = :tid AND code = '1406'
        """), {"vid": new_vid, "tid": tid})
        # Update route runs for 1406
        tmpl = (await db.execute(text(
            "SELECT id FROM route_templates WHERE tenant_id = :tid AND code = '1406'"
        ), {"tid": tid})).first()
        if tmpl:
            await db.execute(text("""
                UPDATE route_runs SET assigned_vehicle_id = :vid
                WHERE tenant_id = :tid AND route_template_id = :rtid
            """), {"vid": new_vid, "tid": tid, "rtid": str(tmpl.id)})
            # Update missions for 1406
            await db.execute(text("""
                UPDATE jobs SET vehicle_id = :vid
                WHERE tenant_id = :tid AND source_route_template_id = :rtid
            """), {"vid": new_vid, "tid": tid, "rtid": str(tmpl.id)})
        print(f"  1406: vehicle changed to DF-314-VL ({new_vid[:8]})")

    # ── 2. Advance missions to realistic statuses ─────────────────
    print("Advancing mission statuses...")

    # Past missions (before today - 3 days) → CLOTUREE (closed)
    r1 = await db.execute(text("""
        UPDATE jobs SET status = 'closed'
        WHERE tenant_id = :tid
          AND date_chargement_prevue < CURRENT_DATE - INTERVAL '3 days'
          AND status = 'planned'
        RETURNING id
    """), {"tid": tid})
    closed = len(r1.fetchall())
    print(f"  {closed} missions → CLOTUREE (past dates)")

    # Missions from 2-3 days ago → LIVREE (delivered)
    r2 = await db.execute(text("""
        UPDATE jobs SET status = 'delivered'
        WHERE tenant_id = :tid
          AND date_chargement_prevue >= CURRENT_DATE - INTERVAL '3 days'
          AND date_chargement_prevue < CURRENT_DATE
          AND status = 'planned'
        RETURNING id
    """), {"tid": tid})
    delivered = len(r2.fetchall())
    print(f"  {delivered} missions → LIVREE (recent)")

    # Today's missions → EN_COURS (in progress)
    r3 = await db.execute(text("""
        UPDATE jobs SET status = 'in_progress'
        WHERE tenant_id = :tid
          AND date_chargement_prevue = CURRENT_DATE
          AND status = 'planned'
        RETURNING id
    """), {"tid": tid})
    in_progress = len(r3.fetchall())
    print(f"  {in_progress} missions → EN_COURS (today)")

    # Tomorrow's missions → AFFECTEE (assigned)
    r4 = await db.execute(text("""
        UPDATE jobs SET status = 'assigned'
        WHERE tenant_id = :tid
          AND date_chargement_prevue = CURRENT_DATE + INTERVAL '1 day'
          AND status = 'planned'
        RETURNING id
    """), {"tid": tid})
    assigned = len(r4.fetchall())
    print(f"  {assigned} missions → AFFECTEE (tomorrow)")

    # Rest stay PLANIFIEE (future)

    # Also update route run statuses to match
    await db.execute(text("""
        UPDATE route_runs SET status = 'COMPLETED'
        WHERE tenant_id = :tid AND service_date < CURRENT_DATE - INTERVAL '3 days' AND status = 'PLANNED'
    """), {"tid": tid})
    await db.execute(text("""
        UPDATE route_runs SET status = 'IN_PROGRESS'
        WHERE tenant_id = :tid AND service_date = CURRENT_DATE AND status = 'PLANNED'
    """), {"tid": tid})
    await db.execute(text("""
        UPDATE route_runs SET status = 'DISPATCHED'
        WHERE tenant_id = :tid AND service_date = CURRENT_DATE + INTERVAL '1 day' AND status = 'PLANNED'
    """), {"tid": tid})

    await db.commit()

    # Summary
    stats = (await db.execute(text("""
        SELECT status, COUNT(*) FROM jobs WHERE tenant_id = :tid GROUP BY status ORDER BY count DESC
    """), {"tid": tid})).fetchall()
    print("\nFinal status distribution:")
    for s in stats:
        print(f"  {s.status:15s} {s.count}")


async def main() -> None:
    async with async_session_factory() as db:
        await fix(db)


if __name__ == "__main__":
    asyncio.run(main())
