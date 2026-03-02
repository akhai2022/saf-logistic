"""Router for Module I — Reporting & KPI (6 endpoints)."""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.tenant import TenantContext, get_tenant
from app.modules.reports.schemas import (
    DashboardResponse,
    ExportRequest,
    ExportResponse,
    FinancialReport,
    FleetReport,
    HrReport,
    KpiCard,
    OperationsReport,
)

router = APIRouter(prefix="/v1/reports", tags=["reports"])

# ── Role → KPI keys mapping ──────────────────────────────────────

ROLE_KPIS: dict[str, list[str]] = {
    "admin": [
        "ca_mensuel", "marge", "taux_conformite", "dso",
        "cout_km", "missions_en_cours", "litiges_ouverts",
    ],
    "exploitation": [
        "missions_en_cours", "pod_delai", "taux_cloture_j1", "litiges_ouverts",
    ],
    "compta": [
        "dso", "balance_agee", "nb_factures_impayees", "ecarts_soustraitants",
    ],
    "rh_paie": [
        "delai_prepaie", "anomalies", "taux_correction", "conformite_conducteurs",
    ],
    "flotte": [
        "taux_conformite_vehicules", "cout_km", "pannes_non_planifiees", "maintenances_a_venir",
    ],
    "lecture_seule": [
        "ca_mensuel", "missions_en_cours", "taux_conformite",
    ],
}

ROLE_ACCESS = {
    "financial": {"admin", "compta"},
    "operations": {"admin", "exploitation"},
    "fleet": {"admin", "flotte"},
    "hr": {"admin", "rh_paie"},
}


async def _get_kpi_value(db: AsyncSession, tid: str, key: str) -> KpiCard:
    """Compute a single KPI value from the database."""
    today = date.today()
    first_of_month = today.replace(day=1)

    if key == "ca_mensuel":
        val = (await db.execute(text("""
            SELECT COALESCE(SUM(total_ht), 0) FROM invoices
            WHERE tenant_id = :tid AND issue_date >= :fom
        """), {"tid": tid, "fom": first_of_month})).scalar() or 0
        return KpiCard(key=key, label="CA mensuel", value=val, unite="EUR")

    elif key == "marge":
        row = (await db.execute(text("""
            SELECT COALESCE(SUM(montant_vente_ht), 0) AS vente,
                   COALESCE(SUM(montant_achat_ht), 0) AS achat
            FROM jobs WHERE tenant_id = :tid AND created_at >= :fom
        """), {"tid": tid, "fom": first_of_month})).first()
        vente = row.vente if row else 0
        achat = row.achat if row else 0
        marge = float(vente - achat) / float(vente) * 100 if vente else 0
        return KpiCard(key=key, label="Marge brute", value=round(marge, 1), unite="%")

    elif key == "missions_en_cours":
        val = (await db.execute(text("""
            SELECT COUNT(*) FROM jobs
            WHERE tenant_id = :tid AND COALESCE(statut, status) IN ('EN_COURS', 'in_progress', 'AFFECTEE', 'assigned')
        """), {"tid": tid})).scalar() or 0
        return KpiCard(key=key, label="Missions en cours", value=val)

    elif key == "litiges_ouverts":
        val = (await db.execute(text("""
            SELECT COUNT(*) FROM disputes
            WHERE tenant_id = :tid AND statut IN ('OUVERT', 'EN_INSTRUCTION')
        """), {"tid": tid})).scalar() or 0
        return KpiCard(key=key, label="Litiges ouverts", value=val)

    elif key == "dso":
        # Simplified DSO: avg days between issue and today for unpaid invoices
        row = (await db.execute(text("""
            SELECT AVG(CURRENT_DATE - issue_date) FROM invoices
            WHERE tenant_id = :tid AND status IN ('sent', 'overdue', 'EMISE')
            AND issue_date IS NOT NULL
        """), {"tid": tid})).scalar()
        return KpiCard(key=key, label="DSO", value=round(float(row or 0), 1), unite="jours")

    elif key == "nb_factures_impayees":
        val = (await db.execute(text("""
            SELECT COUNT(*) FROM invoices
            WHERE tenant_id = :tid AND status IN ('sent', 'overdue', 'EMISE')
        """), {"tid": tid})).scalar() or 0
        return KpiCard(key=key, label="Factures impayees", value=val)

    elif key == "taux_conformite":
        row = (await db.execute(text("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE statut_global = 'OK') AS ok
            FROM compliance_checklists WHERE tenant_id = :tid
        """), {"tid": tid})).first()
        total = row.total if row else 0
        ok = row.ok if row else 0
        pct = (ok / total * 100) if total > 0 else 100
        return KpiCard(key=key, label="Taux conformite", value=round(pct, 1), unite="%")

    elif key == "taux_conformite_vehicules":
        row = (await db.execute(text("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE statut_global = 'OK') AS ok
            FROM compliance_checklists WHERE tenant_id = :tid AND entity_type = 'vehicle'
        """), {"tid": tid})).first()
        total = row.total if row else 0
        ok = row.ok if row else 0
        pct = (ok / total * 100) if total > 0 else 100
        return KpiCard(key=key, label="Conformite vehicules", value=round(pct, 1), unite="%")

    elif key == "conformite_conducteurs":
        row = (await db.execute(text("""
            SELECT COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE statut_global = 'OK') AS ok
            FROM compliance_checklists WHERE tenant_id = :tid AND entity_type = 'driver'
        """), {"tid": tid})).first()
        total = row.total if row else 0
        ok = row.ok if row else 0
        pct = (ok / total * 100) if total > 0 else 100
        return KpiCard(key=key, label="Conformite conducteurs", value=round(pct, 1), unite="%")

    elif key == "cout_km":
        row = (await db.execute(text("""
            SELECT COALESCE(SUM(montant_ht), 0) AS cost FROM vehicle_costs
            WHERE tenant_id = :tid AND date_cout >= :fom
        """), {"tid": tid, "fom": first_of_month})).first()
        km = (await db.execute(text("""
            SELECT COALESCE(SUM(COALESCE(distance_reelle_km, distance_estimee_km, distance_km, 0)), 0)
            FROM jobs WHERE tenant_id = :tid AND created_at >= :fom
        """), {"tid": tid, "fom": first_of_month})).scalar() or 0
        cost = float(row.cost) if row else 0
        ckm = cost / float(km) if km else 0
        return KpiCard(key=key, label="Cout / km", value=round(ckm, 2), unite="EUR/km")

    elif key == "pannes_non_planifiees":
        val = (await db.execute(text("""
            SELECT COUNT(*) FROM maintenance_records
            WHERE tenant_id = :tid AND is_planifie = false AND statut != 'ANNULE'
            AND date_debut >= :fom
        """), {"tid": tid, "fom": first_of_month})).scalar() or 0
        return KpiCard(key=key, label="Pannes non planifiees", value=val)

    elif key == "maintenances_a_venir":
        cutoff = today + timedelta(days=30)
        val = (await db.execute(text("""
            SELECT COUNT(*) FROM maintenance_records
            WHERE tenant_id = :tid AND statut = 'PLANIFIE' AND date_debut <= :cutoff
        """), {"tid": tid, "cutoff": cutoff})).scalar() or 0
        return KpiCard(key=key, label="Maintenances a venir", value=val)

    elif key == "pod_delai":
        return KpiCard(key=key, label="Delai POD moyen", value=0, unite="h")

    elif key == "taux_cloture_j1":
        return KpiCard(key=key, label="Cloture J+1", value=0, unite="%")

    elif key == "balance_agee":
        val = (await db.execute(text("""
            SELECT COALESCE(SUM(total_ttc), 0) FROM invoices
            WHERE tenant_id = :tid AND status IN ('overdue', 'EMISE')
            AND due_date < CURRENT_DATE
        """), {"tid": tid})).scalar() or 0
        return KpiCard(key=key, label="Balance agee", value=val, unite="EUR")

    elif key == "ecarts_soustraitants":
        return KpiCard(key=key, label="Ecarts sous-traitants", value=0, unite="EUR")

    elif key == "delai_prepaie":
        return KpiCard(key=key, label="Delai pre-paie", value=0, unite="jours")

    elif key == "anomalies":
        return KpiCard(key=key, label="Anomalies paie", value=0)

    elif key == "taux_correction":
        return KpiCard(key=key, label="Taux correction", value=0, unite="%")

    return KpiCard(key=key, label=key, value=0)


# =====================================================================
# Endpoints
# =====================================================================

@router.get("/dashboard", response_model=DashboardResponse)
async def dashboard(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = user.get("role", "lecture_seule")
    kpi_keys = ROLE_KPIS.get(role, ROLE_KPIS.get("lecture_seule", []))
    tid = str(tenant.tenant_id)
    kpis = []
    for key in kpi_keys:
        kpi = await _get_kpi_value(db, tid, key)
        kpis.append(kpi)
    return DashboardResponse(role=role, kpis=kpis)


@router.get("/financial", response_model=FinancialReport)
async def financial_report(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = user.get("role", "")
    if role not in ROLE_ACCESS["financial"]:
        raise HTTPException(403, "Acces refuse pour ce rapport")
    tid = str(tenant.tenant_id)
    today = date.today()
    fom = today.replace(day=1)
    foy = today.replace(month=1, day=1)

    ca_m = (await db.execute(text(
        "SELECT COALESCE(SUM(total_ht), 0) FROM invoices WHERE tenant_id = :tid AND issue_date >= :fom"
    ), {"tid": tid, "fom": fom})).scalar() or 0

    ca_y = (await db.execute(text(
        "SELECT COALESCE(SUM(total_ht), 0) FROM invoices WHERE tenant_id = :tid AND issue_date >= :foy"
    ), {"tid": tid, "foy": foy})).scalar() or 0

    row = (await db.execute(text("""
        SELECT COALESCE(SUM(montant_vente_ht), 0) AS v, COALESCE(SUM(montant_achat_ht), 0) AS a
        FROM jobs WHERE tenant_id = :tid AND created_at >= :fom
    """), {"tid": tid, "fom": fom})).first()
    marge = (row.v - row.a) if row else 0
    taux = float(marge) / float(row.v) * 100 if row and row.v else 0

    unpaid = (await db.execute(text("""
        SELECT COUNT(*) AS cnt, AVG(CURRENT_DATE - issue_date) AS dso
        FROM invoices WHERE tenant_id = :tid AND status IN ('sent', 'overdue', 'EMISE')
    """), {"tid": tid})).first()

    nb_emis = (await db.execute(text(
        "SELECT COUNT(*) FROM invoices WHERE tenant_id = :tid AND issue_date >= :fom"
    ), {"tid": tid, "fom": fom})).scalar() or 0

    total_impaye = (await db.execute(text("""
        SELECT COALESCE(SUM(total_ttc), 0) FROM invoices
        WHERE tenant_id = :tid AND status IN ('sent', 'overdue', 'EMISE')
    """), {"tid": tid})).scalar() or 0

    return FinancialReport(
        ca_mensuel=ca_m, ca_cumule_annuel=ca_y,
        marge_brute=marge, taux_marge_pourcent=round(taux, 1),
        dso_jours=round(float(unpaid.dso or 0), 1),
        nb_factures_impayees=unpaid.cnt or 0,
        total_impaye=total_impaye,
        nb_factures_emises_mois=nb_emis,
    )


@router.get("/operations", response_model=OperationsReport)
async def operations_report(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = user.get("role", "")
    if role not in ROLE_ACCESS["operations"]:
        raise HTTPException(403, "Acces refuse pour ce rapport")
    tid = str(tenant.tenant_id)
    fom = date.today().replace(day=1)

    en_cours = (await db.execute(text("""
        SELECT COUNT(*) FROM jobs
        WHERE tenant_id = :tid AND COALESCE(statut, status) IN ('EN_COURS', 'in_progress', 'AFFECTEE', 'assigned')
    """), {"tid": tid})).scalar() or 0

    terminees = (await db.execute(text("""
        SELECT COUNT(*) FROM jobs
        WHERE tenant_id = :tid AND COALESCE(statut, status) IN ('CLOTUREE', 'closed', 'LIVREE', 'delivered')
        AND updated_at >= :fom
    """), {"tid": tid, "fom": fom})).scalar() or 0

    litiges_o = (await db.execute(text("""
        SELECT COUNT(*) FROM disputes WHERE tenant_id = :tid AND statut IN ('OUVERT', 'EN_INSTRUCTION')
    """), {"tid": tid})).scalar() or 0

    litiges_r = (await db.execute(text("""
        SELECT COUNT(*) FROM disputes WHERE tenant_id = :tid AND statut = 'RESOLU'
        AND date_resolution >= :fom
    """), {"tid": tid, "fom": fom})).scalar() or 0

    nb_mois = (await db.execute(text("""
        SELECT COUNT(*) FROM jobs WHERE tenant_id = :tid AND created_at >= :fom
    """), {"tid": tid, "fom": fom})).scalar() or 0

    taux_lit = (litiges_o / nb_mois * 100) if nb_mois else 0

    return OperationsReport(
        missions_en_cours=en_cours,
        missions_terminees_mois=terminees,
        litiges_ouverts=litiges_o,
        litiges_resolus_mois=litiges_r,
        taux_litige=round(taux_lit, 1),
        nb_missions_mois=nb_mois,
    )


@router.get("/fleet", response_model=FleetReport)
async def fleet_report(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = user.get("role", "")
    if role not in ROLE_ACCESS["fleet"]:
        raise HTTPException(403, "Acces refuse pour ce rapport")
    tid = str(tenant.tenant_id)
    fom = date.today().replace(day=1)

    veh = (await db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE statut = 'ACTIF') AS actifs
        FROM vehicles WHERE tenant_id = :tid
    """), {"tid": tid})).first()
    total = veh.total if veh else 0
    actifs = veh.actifs if veh else 0
    dispo = (actifs / total * 100) if total > 0 else 100

    # Compliance
    comp = (await db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE statut_global = 'OK') AS ok
        FROM compliance_checklists WHERE tenant_id = :tid AND entity_type = 'vehicle'
    """), {"tid": tid})).first()
    comp_total = comp.total if comp else 0
    comp_ok = comp.ok if comp else 0
    conf_pct = (comp_ok / comp_total * 100) if comp_total > 0 else 100

    cost = (await db.execute(text(
        "SELECT COALESCE(SUM(montant_ht), 0) FROM vehicle_costs WHERE tenant_id = :tid AND date_cout >= :fom"
    ), {"tid": tid, "fom": fom})).scalar() or 0

    pannes = (await db.execute(text("""
        SELECT COUNT(*) FROM maintenance_records
        WHERE tenant_id = :tid AND is_planifie = false AND statut != 'ANNULE' AND date_debut >= :fom
    """), {"tid": tid, "fom": fom})).scalar() or 0

    cutoff = date.today() + timedelta(days=30)
    upcoming = (await db.execute(text("""
        SELECT COUNT(*) FROM maintenance_records
        WHERE tenant_id = :tid AND statut = 'PLANIFIE' AND date_debut <= :cutoff
    """), {"tid": tid, "cutoff": cutoff})).scalar() or 0

    sinistres = (await db.execute(text("""
        SELECT COUNT(*) FROM vehicle_claims
        WHERE tenant_id = :tid AND statut NOT IN ('CLOS', 'REMBOURSE')
    """), {"tid": tid})).scalar() or 0

    return FleetReport(
        total_vehicles=total,
        taux_disponibilite=round(dispo, 1),
        taux_conformite_vehicules=round(conf_pct, 1),
        cout_total_mois_ht=cost,
        pannes_non_planifiees=pannes,
        maintenances_a_venir=upcoming,
        sinistres_ouverts=sinistres,
    )


@router.get("/hr", response_model=HrReport)
async def hr_report(
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = user.get("role", "")
    if role not in ROLE_ACCESS["hr"]:
        raise HTTPException(403, "Acces refuse pour ce rapport")
    tid = str(tenant.tenant_id)

    nb_drivers = (await db.execute(text(
        "SELECT COUNT(*) FROM drivers WHERE tenant_id = :tid AND statut = 'ACTIF'"
    ), {"tid": tid})).scalar() or 0

    comp = (await db.execute(text("""
        SELECT COUNT(*) AS total,
               COUNT(*) FILTER (WHERE statut_global = 'OK') AS ok
        FROM compliance_checklists WHERE tenant_id = :tid AND entity_type = 'driver'
    """), {"tid": tid})).first()
    comp_total = comp.total if comp else 0
    comp_ok = comp.ok if comp else 0
    conf_pct = (comp_ok / comp_total * 100) if comp_total > 0 else 100

    return HrReport(
        nb_conducteurs_actifs=nb_drivers,
        taux_conformite_conducteurs=round(conf_pct, 1),
    )


@router.post("/export")
async def export_data(
    body: ExportRequest,
    tenant: TenantContext = Depends(get_tenant),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    role = user.get("role", "")
    dataset = body.dataset
    if dataset in ROLE_ACCESS and role not in ROLE_ACCESS[dataset]:
        raise HTTPException(403, "Acces refuse pour cet export")

    tid = str(tenant.tenant_id)
    today = date.today()
    fom = today.replace(day=1)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    if dataset == "fleet":
        writer.writerow(["categorie", "libelle", "date", "montant_ht", "montant_ttc", "vehicule_id"])
        rows = await db.execute(text(
            "SELECT * FROM vehicle_costs WHERE tenant_id = :tid ORDER BY date_cout DESC LIMIT 1000"
        ), {"tid": tid})
        count = 0
        for r in rows.fetchall():
            writer.writerow([r.categorie, r.libelle, r.date_cout, r.montant_ht, r.montant_ttc, r.vehicle_id])
            count += 1
    elif dataset == "operations":
        writer.writerow(["numero", "statut", "client", "date_chargement", "date_livraison", "montant_vente_ht"])
        rows = await db.execute(text(
            "SELECT * FROM jobs WHERE tenant_id = :tid ORDER BY created_at DESC LIMIT 1000"
        ), {"tid": tid})
        count = 0
        for r in rows.fetchall():
            writer.writerow([
                getattr(r, "numero", ""), getattr(r, "statut", getattr(r, "status", "")),
                getattr(r, "client_raison_sociale", ""),
                getattr(r, "date_chargement_prevue", ""), getattr(r, "date_livraison_prevue", ""),
                getattr(r, "montant_vente_ht", ""),
            ])
            count += 1
    elif dataset == "financial":
        writer.writerow(["numero", "statut", "date_emission", "total_ht", "total_ttc", "echeance"])
        rows = await db.execute(text(
            "SELECT * FROM invoices WHERE tenant_id = :tid ORDER BY issue_date DESC LIMIT 1000"
        ), {"tid": tid})
        count = 0
        for r in rows.fetchall():
            writer.writerow([r.invoice_number, r.status, r.issue_date, r.total_ht, r.total_ttc, r.due_date])
            count += 1
    elif dataset == "hr":
        writer.writerow(["matricule", "nom", "prenom", "statut", "conformite"])
        rows = await db.execute(text(
            "SELECT * FROM drivers WHERE tenant_id = :tid ORDER BY nom LIMIT 1000"
        ), {"tid": tid})
        count = 0
        for r in rows.fetchall():
            writer.writerow([r.matricule, r.nom, r.prenom, r.statut, r.conformite_statut])
            count += 1
    else:
        raise HTTPException(422, f"Dataset inconnu: {dataset}")

    output.seek(0)
    filename = f"export_{dataset}_{today.isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
