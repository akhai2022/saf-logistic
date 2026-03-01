"""Module C — Missions / Dossiers Transport, POD, Disputes.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Expand jobs table → full Mission entity
    # ------------------------------------------------------------------
    op.add_column("jobs", sa.Column("numero", sa.String(30)))
    op.add_column("jobs", sa.Column("reference_client", sa.String(100)))
    op.add_column("jobs", sa.Column("client_raison_sociale", sa.String(255)))
    op.add_column("jobs", sa.Column("type_mission", sa.String(30), server_default=sa.text("'LOT_COMPLET'")))
    op.add_column("jobs", sa.Column("priorite", sa.String(20), server_default=sa.text("'NORMALE'")))

    op.add_column("jobs", sa.Column("date_chargement_prevue", sa.DateTime(timezone=True)))
    op.add_column("jobs", sa.Column("date_chargement_reelle", sa.DateTime(timezone=True)))
    op.add_column("jobs", sa.Column("date_livraison_prevue", sa.DateTime(timezone=True)))
    op.add_column("jobs", sa.Column("date_livraison_reelle", sa.DateTime(timezone=True)))
    op.add_column("jobs", sa.Column("date_cloture", sa.DateTime(timezone=True)))

    op.add_column("jobs", sa.Column("adresse_chargement_id", sa.UUID(), sa.ForeignKey("client_addresses.id", ondelete="SET NULL")))
    op.add_column("jobs", sa.Column("adresse_chargement_libre", sa.Text()))  # JSON string
    op.add_column("jobs", sa.Column("adresse_chargement_contact", sa.String(200)))
    op.add_column("jobs", sa.Column("adresse_chargement_instructions", sa.Text()))

    op.add_column("jobs", sa.Column("distance_estimee_km", sa.Numeric(8, 1)))
    op.add_column("jobs", sa.Column("distance_reelle_km", sa.Numeric(8, 1)))

    op.add_column("jobs", sa.Column("trailer_id", sa.UUID(), sa.ForeignKey("vehicles.id", ondelete="SET NULL")))
    op.add_column("jobs", sa.Column("subcontractor_id", sa.UUID(), sa.ForeignKey("subcontractors.id", ondelete="SET NULL")))
    op.add_column("jobs", sa.Column("is_subcontracted", sa.Boolean(), server_default=sa.text("false")))

    op.add_column("jobs", sa.Column("montant_vente_ht", sa.Numeric(12, 2)))
    op.add_column("jobs", sa.Column("montant_achat_ht", sa.Numeric(12, 2)))
    op.add_column("jobs", sa.Column("montant_tva", sa.Numeric(12, 2)))
    op.add_column("jobs", sa.Column("montant_vente_ttc", sa.Numeric(12, 2)))
    op.add_column("jobs", sa.Column("marge_brute", sa.Numeric(12, 2)))

    op.add_column("jobs", sa.Column("contraintes", sa.Text()))  # JSON string
    op.add_column("jobs", sa.Column("notes_exploitation", sa.Text()))
    op.add_column("jobs", sa.Column("notes_internes", sa.Text()))

    op.add_column("jobs", sa.Column("facture_id", sa.UUID()))
    op.add_column("jobs", sa.Column("avoir_id", sa.UUID()))
    op.add_column("jobs", sa.Column("centre_cout_id", sa.UUID()))
    op.add_column("jobs", sa.Column("created_by", sa.UUID()))
    op.add_column("jobs", sa.Column("updated_by", sa.UUID()))

    # Migrate: copy old pickup_date → date_chargement_prevue, delivery_date → date_livraison_prevue
    op.execute("""
        UPDATE jobs SET
            date_chargement_prevue = pickup_date,
            date_livraison_prevue = delivery_date,
            distance_estimee_km = distance_km,
            date_cloture = closed_at
        WHERE pickup_date IS NOT NULL OR delivery_date IS NOT NULL
    """)

    # Add indexes
    op.create_index("ix_jobs_numero", "jobs", ["tenant_id", "numero"], unique=True)
    op.create_index("ix_jobs_customer", "jobs", ["tenant_id", "customer_id"])
    op.create_index("ix_jobs_subcontractor", "jobs", ["subcontractor_id"])

    # ------------------------------------------------------------------
    # Mission Delivery Points
    # ------------------------------------------------------------------
    op.create_table(
        "mission_delivery_points",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("adresse_id", sa.UUID(), sa.ForeignKey("client_addresses.id", ondelete="SET NULL")),
        sa.Column("adresse_libre", sa.Text()),  # JSON
        sa.Column("contact_nom", sa.String(100)),
        sa.Column("contact_telephone", sa.String(20)),
        sa.Column("date_livraison_prevue", sa.DateTime(timezone=True)),
        sa.Column("date_livraison_reelle", sa.DateTime(timezone=True)),
        sa.Column("instructions", sa.Text()),
        sa.Column("statut", sa.String(20), server_default=sa.text("'EN_ATTENTE'"), nullable=False),
        sa.Column("motif_echec", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_delivery_points_mission", "mission_delivery_points", ["mission_id"])

    # ------------------------------------------------------------------
    # Mission Goods
    # ------------------------------------------------------------------
    op.create_table(
        "mission_goods",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delivery_point_id", sa.UUID(), sa.ForeignKey("mission_delivery_points.id", ondelete="SET NULL")),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("nature", sa.String(30), nullable=False),
        sa.Column("quantite", sa.Numeric(10, 2), nullable=False),
        sa.Column("unite", sa.String(20), nullable=False),
        sa.Column("poids_brut_kg", sa.Numeric(10, 2), nullable=False),
        sa.Column("poids_net_kg", sa.Numeric(10, 2)),
        sa.Column("volume_m3", sa.Numeric(8, 2)),
        sa.Column("longueur_m", sa.Numeric(5, 2)),
        sa.Column("largeur_m", sa.Numeric(5, 2)),
        sa.Column("hauteur_m", sa.Numeric(5, 2)),
        sa.Column("valeur_declaree_eur", sa.Numeric(12, 2)),
        sa.Column("adr_classe", sa.String(5)),
        sa.Column("adr_numero_onu", sa.String(10)),
        sa.Column("adr_designation", sa.String(255)),
        sa.Column("temperature_min", sa.Numeric(5, 1)),
        sa.Column("temperature_max", sa.Numeric(5, 1)),
        sa.Column("references_colis", sa.Text()),  # JSON
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_mission_goods_mission", "mission_goods", ["mission_id"])

    # ------------------------------------------------------------------
    # Proof of Delivery
    # ------------------------------------------------------------------
    op.create_table(
        "proof_of_delivery",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mission_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delivery_point_id", sa.UUID(), sa.ForeignKey("mission_delivery_points.id", ondelete="SET NULL")),
        sa.Column("type", sa.String(20), nullable=False),  # PHOTO, PDF_SCAN, E_SIGNATURE
        sa.Column("fichier_s3_key", sa.String(500), nullable=False),
        sa.Column("fichier_nom_original", sa.String(255), nullable=False),
        sa.Column("fichier_taille_octets", sa.Integer(), nullable=False),
        sa.Column("fichier_mime_type", sa.String(50), nullable=False),
        sa.Column("date_upload", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("uploaded_by", sa.UUID(), nullable=False),
        sa.Column("uploaded_by_role", sa.String(30)),
        sa.Column("geoloc_latitude", sa.Numeric(10, 7)),
        sa.Column("geoloc_longitude", sa.Numeric(10, 7)),
        sa.Column("geoloc_precision_m", sa.Integer()),
        sa.Column("has_reserves", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reserves_texte", sa.Text()),
        sa.Column("reserves_categorie", sa.String(30)),  # AVARIE, MANQUANT, RETARD, COLIS_ENDOMMAGE, AUTRE
        sa.Column("statut", sa.String(20), server_default=sa.text("'EN_ATTENTE'"), nullable=False),
        sa.Column("date_validation", sa.DateTime(timezone=True)),
        sa.Column("validated_by", sa.UUID()),
        sa.Column("motif_rejet", sa.Text()),
        sa.Column("e_signature_data", sa.Text()),  # JSON
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_pod_mission", "proof_of_delivery", ["mission_id"])

    # ------------------------------------------------------------------
    # Disputes
    # ------------------------------------------------------------------
    op.create_table(
        "disputes",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("numero", sa.String(30)),
        sa.Column("mission_id", sa.UUID(), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("responsabilite", sa.String(30), nullable=False),
        sa.Column("responsable_entity_id", sa.UUID()),
        sa.Column("montant_estime_eur", sa.Numeric(12, 2)),
        sa.Column("montant_retenu_eur", sa.Numeric(12, 2)),
        sa.Column("statut", sa.String(30), server_default=sa.text("'OUVERT'"), nullable=False),
        sa.Column("date_ouverture", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("date_resolution", sa.DateTime(timezone=True)),
        sa.Column("resolution_texte", sa.Text()),
        sa.Column("impact_facturation", sa.String(30)),
        sa.Column("avoir_id", sa.UUID()),
        sa.Column("opened_by", sa.UUID(), nullable=False),
        sa.Column("assigned_to", sa.UUID()),
        sa.Column("notes_internes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_disputes_mission", "disputes", ["mission_id"])
    op.create_index("ix_disputes_tenant", "disputes", ["tenant_id"])
    op.create_index("ix_disputes_numero", "disputes", ["tenant_id", "numero"], unique=True)

    # ------------------------------------------------------------------
    # Dispute Attachments
    # ------------------------------------------------------------------
    op.create_table(
        "dispute_attachments",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dispute_id", sa.UUID(), sa.ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fichier_s3_key", sa.String(500), nullable=False),
        sa.Column("fichier_nom_original", sa.String(255), nullable=False),
        sa.Column("fichier_taille_octets", sa.Integer(), nullable=False),
        sa.Column("fichier_mime_type", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("uploaded_by", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_dispute_attachments_dispute", "dispute_attachments", ["dispute_id"])


def downgrade() -> None:
    op.drop_table("dispute_attachments")
    op.drop_table("disputes")
    op.drop_table("proof_of_delivery")
    op.drop_table("mission_goods")
    op.drop_table("mission_delivery_points")

    # Remove indexes
    op.drop_index("ix_jobs_subcontractor")
    op.drop_index("ix_jobs_customer")
    op.drop_index("ix_jobs_numero")

    # Remove added columns from jobs
    for col in [
        "numero", "reference_client", "client_raison_sociale", "type_mission", "priorite",
        "date_chargement_prevue", "date_chargement_reelle",
        "date_livraison_prevue", "date_livraison_reelle", "date_cloture",
        "adresse_chargement_id", "adresse_chargement_libre",
        "adresse_chargement_contact", "adresse_chargement_instructions",
        "distance_estimee_km", "distance_reelle_km",
        "trailer_id", "subcontractor_id", "is_subcontracted",
        "montant_vente_ht", "montant_achat_ht", "montant_tva", "montant_vente_ttc", "marge_brute",
        "contraintes", "notes_exploitation", "notes_internes",
        "facture_id", "avoir_id", "centre_cout_id", "created_by", "updated_by",
    ]:
        op.drop_column("jobs", col)
