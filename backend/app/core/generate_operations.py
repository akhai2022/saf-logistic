"""
Generate operational data for SAF Logistique.

1. Assigns default drivers + vehicles to route templates (from SAF planning data)
2. Generates route runs + missions for April 2026

Usage:
  python -m app.core.generate_operations
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory

TENANT_ID = "10000000-0000-0000-0000-000000000001"

# Driver-Vehicle-Route assignments from SAF January 2026 planning sheet
# Format: route_code → (driver_nom, vehicle_plate, montant_vente_ht, montant_achat_ht)
ASSIGNMENTS = {
    "1029": ("BOUKZINE", "EB-007-HK", 450, 320),
    "1013": ("GOMIS", "BZ-627-AM", 420, 300),
    "1016": ("EL IDRISSI", "CT-529-GA", 420, 300),
    "1017": ("BENALLOU", "AW-639-SE", 420, 300),
    "1012": ("DAHDOUD", "CH-398-HL", 400, 290),
    "095174": ("KONATE", "BF-304-TQ", 500, 350),
    "095237": ("OULAIN", "CS-830-NH", 500, 350),
    "095238": ("WAMBA", "AC-013-YA", 500, 350),
    "174": ("MADJID", "CB-631-JN", 480, 340),
    "1406": ("CHENHAOUI", "AW-639-SE", 450, 320),
}


def _expand_dates(recurrence: str, start: date, end: date) -> list[date]:
    dates = []
    d = start
    while d <= end:
        wd = d.weekday()
        if recurrence == "LUN_VEN" and wd < 5:
            dates.append(d)
        elif recurrence == "QUOTIDIENNE":
            dates.append(d)
        elif recurrence == "LUN_SAM" and wd < 6:
            dates.append(d)
        d += timedelta(days=1)
    return dates


async def generate(db: AsyncSession) -> None:
    tid = TENANT_ID

    # ── 1. Get all templates ─────────────────────────────────────────
    templates = (await db.execute(text(
        "SELECT id, code, recurrence_rule, customer_id FROM route_templates WHERE tenant_id = :tid"
    ), {"tid": tid})).fetchall()

    template_map = {t.code: t for t in templates}

    # ── 2. Get all drivers (by nom) ──────────────────────────────────
    drivers = (await db.execute(text(
        "SELECT id, nom FROM drivers WHERE tenant_id = :tid"
    ), {"tid": tid})).fetchall()
    driver_map = {d.nom.upper(): str(d.id) for d in drivers if d.nom}

    # ── 3. Get all vehicles (by plate) ───────────────────────────────
    vehicles = (await db.execute(text(
        "SELECT id, COALESCE(immatriculation, plate_number) AS plate FROM vehicles WHERE tenant_id = :tid"
    ), {"tid": tid})).fetchall()
    vehicle_map = {v.plate: str(v.id) for v in vehicles if v.plate}

    # ── 4. Assign drivers + vehicles to templates ────────────────────
    print("Assigning drivers and vehicles to route templates...")
    assigned = 0
    for code, (driver_nom, vehicle_plate, sale, purchase) in ASSIGNMENTS.items():
        tmpl = template_map.get(code)
        if not tmpl:
            print(f"  SKIP: template {code} not found")
            continue

        driver_id = driver_map.get(driver_nom.upper())
        vehicle_id = vehicle_map.get(vehicle_plate)

        if not driver_id:
            print(f"  WARN: driver {driver_nom} not found")
        if not vehicle_id:
            print(f"  WARN: vehicle {vehicle_plate} not found")

        await db.execute(text("""
            UPDATE route_templates SET
                default_driver_id = :did,
                default_vehicle_id = :vid,
                default_sale_amount_ht = :sale,
                default_purchase_amount_ht = :purchase,
                updated_at = NOW()
            WHERE id = :id AND tenant_id = :tid
        """), {
            "id": str(tmpl.id), "tid": tid,
            "did": driver_id, "vid": vehicle_id,
            "sale": sale, "purchase": purchase,
        })
        assigned += 1
        print(f"  {code}: {driver_nom} + {vehicle_plate} ({sale}€/{purchase}€)")

    await db.commit()
    print(f"  → {assigned} templates updated")

    # ── 5. Generate runs + missions for April 2026 ───────────────────
    gen_start = date(2026, 4, 1)
    gen_end = date(2026, 4, 30)
    print(f"\nGenerating runs + missions for {gen_start} → {gen_end}...")

    total_runs = 0
    total_missions = 0

    # Get mission counter
    last_num = (await db.execute(text(
        "SELECT numero FROM jobs WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 1"
    ), {"tid": tid})).scalar()
    counter = 1
    if last_num:
        try:
            counter = int(last_num.split("-")[-1]) + 1
        except (ValueError, IndexError):
            pass

    for code, (driver_nom, vehicle_plate, sale, purchase) in ASSIGNMENTS.items():
        tmpl = template_map.get(code)
        if not tmpl:
            continue

        driver_id = driver_map.get(driver_nom.upper())
        vehicle_id = vehicle_map.get(vehicle_plate)
        exec_dates = _expand_dates(tmpl.recurrence_rule, gen_start, gen_end)

        for exec_date in exec_dates:
            run_code = f"RUN-{code}-{exec_date.isoformat()}"

            # Idempotency
            existing = (await db.execute(text(
                "SELECT id FROM route_runs WHERE code = :c AND tenant_id = :tid"
            ), {"c": run_code, "tid": tid})).first()
            if existing:
                continue

            run_id = uuid.uuid4()
            await db.execute(text("""
                INSERT INTO route_runs (
                    id, tenant_id, route_template_id, code, service_date, status,
                    assigned_driver_id, assigned_vehicle_id, notes
                ) VALUES (
                    :id, :tid, :rtid, :code, :sd, 'PLANNED',
                    :did, :vid, :notes
                )
            """), {
                "id": str(run_id), "tid": tid, "rtid": str(tmpl.id),
                "code": run_code, "sd": exec_date,
                "did": driver_id, "vid": vehicle_id,
                "notes": f"Genere automatiquement — tournee {code}",
            })
            total_runs += 1

            # Create mission
            mission_id = uuid.uuid4()
            mission_code = f"MIS-{exec_date.year}-{exec_date.month:02d}-{counter:05d}"
            counter += 1

            await db.execute(text("""
                INSERT INTO jobs (
                    id, tenant_id, numero, customer_id, type_mission,
                    date_chargement_prevue, date_livraison_prevue,
                    driver_id, vehicle_id,
                    montant_vente_ht, montant_achat_ht,
                    notes_exploitation, source_type,
                    source_route_template_id, source_route_run_id,
                    status
                ) VALUES (
                    :id, :tid, :num, :cid, 'LOT_COMPLET',
                    :date_charge, :date_livre,
                    :did, :vid,
                    :sale, :purchase,
                    :notes, 'GENERATED_FROM_TEMPLATE',
                    :rtid, :rrid,
                    'planned'
                )
            """), {
                "id": str(mission_id), "tid": tid, "num": mission_code,
                "cid": str(tmpl.customer_id) if tmpl.customer_id else None,
                "date_charge": exec_date, "date_livre": exec_date,
                "did": driver_id, "vid": vehicle_id,
                "sale": sale, "purchase": purchase,
                "notes": f"Tournee {code} — {exec_date.isoformat()}",
                "rtid": str(tmpl.id), "rrid": str(run_id),
            })
            total_missions += 1

            # Link mission to run
            await db.execute(text("""
                INSERT INTO route_run_missions (id, tenant_id, route_run_id, mission_id, sequence)
                VALUES (:id, :tid, :rrid, :mid, 1)
            """), {
                "id": str(uuid.uuid4()), "tid": tid,
                "rrid": str(run_id), "mid": str(mission_id),
            })

    await db.commit()

    print(f"\n{'=' * 60}")
    print(f"Operations generated successfully.")
    print(f"  Route runs:  {total_runs}")
    print(f"  Missions:    {total_missions}")
    print(f"  Period:      {gen_start} → {gen_end}")
    print(f"{'=' * 60}")
    print(f"\nRevenue estimate: {total_missions * 450:.0f}€ (avg 450€/mission)")
    print(f"Cost estimate:    {total_missions * 320:.0f}€ (avg 320€/mission)")
    print(f"Margin estimate:  {total_missions * 130:.0f}€")


async def main() -> None:
    async with async_session_factory() as db:
        await generate(db)


if __name__ == "__main__":
    asyncio.run(main())
