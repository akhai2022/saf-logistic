"""Add fields required by SAF Logistique integration data.

Drivers: fuel card, medical visits, site, licence intracom
Vehicles: inspections, insurance, ADR, acquisition details
New tables: traffic_fines, driver_leaves

Revision ID: 0010
Revises: 0009
Create Date: 2026-03-27 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Drivers: fuel card, medical, site ────────────────────────────
    op.add_column("drivers", sa.Column("carte_gazoil_ref", sa.String(100)))
    op.add_column("drivers", sa.Column("carte_gazoil_enseigne", sa.String(50)))
    op.add_column("drivers", sa.Column("medecine_travail_dernier_rdv", sa.Date()))
    op.add_column("drivers", sa.Column("medecine_travail_prochain_rdv", sa.Date()))
    op.add_column("drivers", sa.Column("site_affectation", sa.String(100)))
    op.add_column("drivers", sa.Column("licence_intracom_numero", sa.String(20)))
    op.add_column("drivers", sa.Column("email_personnel", sa.String(255)))
    op.add_column("drivers", sa.Column("permis_numero", sa.String(30)))

    # ── Vehicles: inspections, insurance, ADR, acquisition ───────────
    # vin already exists in 0001
    op.add_column("vehicles", sa.Column("nombre_places", sa.Integer()))
    op.add_column("vehicles", sa.Column("mode_achat", sa.String(30)))
    op.add_column("vehicles", sa.Column("valeur_assuree_ht", sa.Numeric(12, 2)))
    op.add_column("vehicles", sa.Column("telematique", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("vehicles", sa.Column("reference_client", sa.String(100)))
    op.add_column("vehicles", sa.Column("date_entree_flotte", sa.Date()))
    op.add_column("vehicles", sa.Column("date_sortie_flotte", sa.Date()))
    op.add_column("vehicles", sa.Column("presence_matiere_dangereuse", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("vehicles", sa.Column("assurance_compagnie", sa.String(100)))
    op.add_column("vehicles", sa.Column("assurance_numero_police", sa.String(50)))
    op.add_column("vehicles", sa.Column("controle_technique_date", sa.Date()))
    op.add_column("vehicles", sa.Column("limiteur_vitesse_date", sa.Date()))
    op.add_column("vehicles", sa.Column("tachygraphe_date", sa.Date()))
    op.add_column("vehicles", sa.Column("siren_proprietaire", sa.String(9)))

    # ── Traffic fines ────────────────────────────────────────────────
    op.create_table(
        "traffic_fines",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date_infraction", sa.Date()),
        sa.Column("lieu", sa.String(255)),
        sa.Column("immatriculation", sa.String(15)),
        sa.Column("vehicle_id", sa.UUID(), sa.ForeignKey("vehicles.id", ondelete="SET NULL")),
        sa.Column("driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="SET NULL")),
        sa.Column("descriptif", sa.Text()),
        sa.Column("numero_avis", sa.String(50)),
        sa.Column("montant", sa.Numeric(10, 2)),
        sa.Column("etat_paiement", sa.String(30), server_default=sa.text("'A_PAYER'")),
        sa.Column("etat_dossier", sa.String(30), server_default=sa.text("'OUVERT'")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_traffic_fines_tenant", "traffic_fines", ["tenant_id"])
    op.create_index("ix_traffic_fines_vehicle", "traffic_fines", ["vehicle_id"])

    # ── Driver leaves ────────────────────────────────────────────────
    op.create_table(
        "driver_leaves",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type_conge", sa.String(30), server_default=sa.text("'CP'")),
        sa.Column("date_debut", sa.Date(), nullable=False),
        sa.Column("date_fin", sa.Date(), nullable=False),
        sa.Column("statut", sa.String(20), server_default=sa.text("'VALIDE'")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_driver_leaves_tenant", "driver_leaves", ["tenant_id"])
    op.create_index("ix_driver_leaves_driver", "driver_leaves", ["driver_id"])

    # ── Driver infractions (monthly tracking) ────────────────────────
    op.create_table(
        "driver_infractions",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", sa.UUID(), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mois", sa.Integer(), nullable=False),
        sa.Column("annee", sa.Integer(), nullable=False),
        sa.Column("nb_infractions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("nb_anomalies", sa.Integer(), server_default=sa.text("0")),
        sa.Column("details", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_driver_infractions_tenant", "driver_infractions", ["tenant_id"])
    op.create_index("ix_driver_infractions_driver", "driver_infractions", ["driver_id"])
    op.create_unique_constraint("uq_driver_infractions_period", "driver_infractions",
                                ["driver_id", "mois", "annee"])


def downgrade() -> None:
    op.drop_table("driver_infractions")
    op.drop_table("driver_leaves")
    op.drop_table("traffic_fines")

    for col in ["nombre_places", "mode_achat", "valeur_assuree_ht", "telematique",
                "reference_client", "date_entree_flotte", "date_sortie_flotte",
                "presence_matiere_dangereuse", "assurance_compagnie", "assurance_numero_police",
                "controle_technique_date", "limiteur_vitesse_date", "tachygraphe_date",
                "siren_proprietaire"]:
        op.drop_column("vehicles", col)

    for col in ["carte_gazoil_ref", "carte_gazoil_enseigne", "medecine_travail_dernier_rdv",
                "medecine_travail_prochain_rdv", "site_affectation", "licence_intracom_numero",
                "email_personnel", "permis_numero"]:
        op.drop_column("drivers", col)
