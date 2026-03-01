"""Module B — Referentiels Metier: expand clients, drivers, vehicles; add subcontractors.

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-28 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. ALTER customers — add Module B fields
    # ------------------------------------------------------------------
    op.add_column("customers", sa.Column("code", sa.String(20)))
    op.add_column("customers", sa.Column("raison_sociale", sa.String(255)))
    op.add_column("customers", sa.Column("nom_commercial", sa.String(255)))
    op.add_column("customers", sa.Column("siret", sa.String(14)))
    op.add_column("customers", sa.Column("tva_intracom", sa.String(13)))
    op.add_column("customers", sa.Column("code_naf", sa.String(6)))
    op.add_column("customers", sa.Column("adresse_facturation_ligne1", sa.String(255)))
    op.add_column("customers", sa.Column("adresse_facturation_ligne2", sa.String(255)))
    op.add_column("customers", sa.Column("adresse_facturation_cp", sa.String(5)))
    op.add_column("customers", sa.Column("adresse_facturation_ville", sa.String(100)))
    op.add_column("customers", sa.Column("adresse_facturation_pays", sa.String(2), server_default=sa.text("'FR'")))
    op.add_column("customers", sa.Column("telephone", sa.String(20)))
    op.add_column("customers", sa.Column("email", sa.String(255)))
    op.add_column("customers", sa.Column("site_web", sa.String(255)))
    op.add_column("customers", sa.Column("delai_paiement_jours", sa.Integer(), server_default=sa.text("30")))
    op.add_column("customers", sa.Column("mode_paiement", sa.String(30), server_default=sa.text("'VIREMENT'")))
    op.add_column("customers", sa.Column("condition_paiement_texte", sa.String(255)))
    op.add_column("customers", sa.Column("escompte_pourcent", sa.Numeric(5, 2)))
    op.add_column("customers", sa.Column("penalite_retard_pourcent", sa.Numeric(5, 2)))
    op.add_column("customers", sa.Column("indemnite_recouvrement", sa.Numeric(10, 2)))
    op.add_column("customers", sa.Column("plafond_encours", sa.Numeric(15, 2)))
    op.add_column("customers", sa.Column("sla_delai_livraison_heures", sa.Integer()))
    op.add_column("customers", sa.Column("sla_taux_service_pourcent", sa.Numeric(5, 2)))
    op.add_column("customers", sa.Column("sla_penalite_texte", sa.Text()))
    op.add_column("customers", sa.Column("agency_ids", sa.JSON()))
    op.add_column("customers", sa.Column("notes", sa.Text()))
    op.add_column("customers", sa.Column("statut", sa.String(20), server_default=sa.text("'ACTIF'")))
    op.add_column("customers", sa.Column("date_debut_relation", sa.Date()))
    op.add_column("customers", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.add_column("customers", sa.Column("created_by", sa.UUID()))
    op.add_column("customers", sa.Column("updated_by", sa.UUID()))

    # Migrate existing data: name → raison_sociale, address → adresse_facturation_ligne1
    op.execute("""
        UPDATE customers
        SET raison_sociale = name,
            adresse_facturation_ligne1 = address,
            delai_paiement_jours = payment_terms_days
        WHERE raison_sociale IS NULL
    """)

    op.create_unique_constraint("uq_customers_tenant_code", "customers", ["tenant_id", "code"])

    # ------------------------------------------------------------------
    # 2. CREATE client_contacts
    # ------------------------------------------------------------------
    op.create_table(
        "client_contacts",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("civilite", sa.String(10)),
        sa.Column("nom", sa.String(100), nullable=False),
        sa.Column("prenom", sa.String(100), nullable=False),
        sa.Column("fonction", sa.String(100)),
        sa.Column("email", sa.String(255)),
        sa.Column("telephone_fixe", sa.String(20)),
        sa.Column("telephone_mobile", sa.String(20)),
        sa.Column("is_contact_principal", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_contact_facturation", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_contact_exploitation", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("notes", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_client_contacts_client", "client_contacts", ["client_id"])
    op.create_index("ix_client_contacts_tenant", "client_contacts", ["tenant_id"])

    # ------------------------------------------------------------------
    # 3. CREATE client_addresses
    # ------------------------------------------------------------------
    op.create_table(
        "client_addresses",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_id", sa.UUID(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("libelle", sa.String(100), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),  # LIVRAISON, CHARGEMENT, MIXTE
        sa.Column("adresse_ligne1", sa.String(255), nullable=False),
        sa.Column("adresse_ligne2", sa.String(255)),
        sa.Column("code_postal", sa.String(5), nullable=False),
        sa.Column("ville", sa.String(100), nullable=False),
        sa.Column("pays", sa.String(2), server_default=sa.text("'FR'")),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("contact_site_nom", sa.String(100)),
        sa.Column("contact_site_telephone", sa.String(20)),
        sa.Column("horaires_ouverture", sa.String(255)),
        sa.Column("instructions_acces", sa.Text()),
        sa.Column("contraintes", sa.JSON()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_client_addresses_client", "client_addresses", ["client_id"])
    op.create_index("ix_client_addresses_tenant", "client_addresses", ["tenant_id"])

    # ------------------------------------------------------------------
    # 4. CREATE subcontractors
    # ------------------------------------------------------------------
    op.create_table(
        "subcontractors",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("raison_sociale", sa.String(255), nullable=False),
        sa.Column("siret", sa.String(14), nullable=False),
        sa.Column("siren", sa.String(9)),
        sa.Column("tva_intracom", sa.String(13)),
        sa.Column("licence_transport", sa.String(50)),
        sa.Column("adresse_ligne1", sa.String(255), nullable=False),
        sa.Column("adresse_ligne2", sa.String(255)),
        sa.Column("code_postal", sa.String(5), nullable=False),
        sa.Column("ville", sa.String(100), nullable=False),
        sa.Column("pays", sa.String(2), server_default=sa.text("'FR'")),
        sa.Column("telephone", sa.String(20)),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("contact_principal_nom", sa.String(100)),
        sa.Column("contact_principal_telephone", sa.String(20)),
        sa.Column("contact_principal_email", sa.String(255)),
        sa.Column("zones_geographiques", sa.JSON()),
        sa.Column("types_vehicules_disponibles", sa.JSON()),
        sa.Column("specialites", sa.JSON()),
        sa.Column("delai_paiement_jours", sa.Integer(), server_default=sa.text("45")),
        sa.Column("mode_paiement", sa.String(30), server_default=sa.text("'VIREMENT'")),
        sa.Column("rib_iban", sa.String(34)),
        sa.Column("rib_bic", sa.String(11)),
        sa.Column("statut", sa.String(30), server_default=sa.text("'EN_COURS_VALIDATION'")),
        sa.Column("conformite_statut", sa.String(20), server_default=sa.text("'A_REGULARISER'")),
        sa.Column("note_qualite", sa.Numeric(3, 1)),
        sa.Column("agency_ids", sa.JSON()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", sa.UUID()),
        sa.Column("updated_by", sa.UUID()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_subcontractors_tenant_code"),
    )
    op.create_index("ix_subcontractors_tenant", "subcontractors", ["tenant_id"])

    # ------------------------------------------------------------------
    # 5. CREATE subcontractor_contracts
    # ------------------------------------------------------------------
    op.create_table(
        "subcontractor_contracts",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", sa.UUID(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subcontractor_id", sa.UUID(), sa.ForeignKey("subcontractors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reference", sa.String(50), nullable=False),
        sa.Column("type_prestation", sa.String(30), nullable=False),
        sa.Column("date_debut", sa.Date(), nullable=False),
        sa.Column("date_fin", sa.Date()),
        sa.Column("tacite_reconduction", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("preavis_resiliation_jours", sa.Integer()),
        sa.Column("document_s3_key", sa.String(500)),
        sa.Column("tarification", sa.JSON()),
        sa.Column("statut", sa.String(20), server_default=sa.text("'BROUILLON'")),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_subcontractor_contracts_sub", "subcontractor_contracts", ["subcontractor_id"])
    op.create_index("ix_subcontractor_contracts_tenant", "subcontractor_contracts", ["tenant_id"])

    # ------------------------------------------------------------------
    # 6. ALTER drivers — add Module B fields
    # ------------------------------------------------------------------
    op.add_column("drivers", sa.Column("civilite", sa.String(10)))
    op.add_column("drivers", sa.Column("nom", sa.String(100)))
    op.add_column("drivers", sa.Column("prenom", sa.String(100)))
    op.add_column("drivers", sa.Column("date_naissance", sa.Date()))
    op.add_column("drivers", sa.Column("lieu_naissance", sa.String(100)))
    op.add_column("drivers", sa.Column("nationalite", sa.String(2)))
    op.add_column("drivers", sa.Column("nir", sa.String(15)))
    op.add_column("drivers", sa.Column("adresse_ligne1", sa.String(255)))
    op.add_column("drivers", sa.Column("adresse_ligne2", sa.String(255)))
    op.add_column("drivers", sa.Column("code_postal", sa.String(5)))
    op.add_column("drivers", sa.Column("ville", sa.String(100)))
    op.add_column("drivers", sa.Column("pays", sa.String(2), server_default=sa.text("'FR'")))
    op.add_column("drivers", sa.Column("telephone_mobile", sa.String(20)))
    op.add_column("drivers", sa.Column("statut_emploi", sa.String(20), server_default=sa.text("'SALARIE'")))
    op.add_column("drivers", sa.Column("agence_interim_nom", sa.String(255)))
    op.add_column("drivers", sa.Column("agence_interim_contact", sa.String(255)))
    op.add_column("drivers", sa.Column("type_contrat", sa.String(20), server_default=sa.text("'CDI'")))
    op.add_column("drivers", sa.Column("date_entree", sa.Date()))
    op.add_column("drivers", sa.Column("date_sortie", sa.Date()))
    op.add_column("drivers", sa.Column("motif_sortie", sa.String(30)))
    op.add_column("drivers", sa.Column("poste", sa.String(100)))
    op.add_column("drivers", sa.Column("categorie_permis", sa.JSON()))
    op.add_column("drivers", sa.Column("coefficient", sa.String(10)))
    op.add_column("drivers", sa.Column("groupe", sa.String(10)))
    op.add_column("drivers", sa.Column("salaire_base_mensuel", sa.Numeric(10, 2)))
    op.add_column("drivers", sa.Column("taux_horaire", sa.Numeric(8, 4)))
    op.add_column("drivers", sa.Column("qualification_fimo", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("drivers", sa.Column("qualification_fco", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("drivers", sa.Column("qualification_adr", sa.Boolean(), server_default=sa.text("false")))
    op.add_column("drivers", sa.Column("qualification_adr_classes", sa.JSON()))
    op.add_column("drivers", sa.Column("carte_conducteur_numero", sa.String(20)))
    op.add_column("drivers", sa.Column("centre_cout_id", sa.UUID()))
    op.add_column("drivers", sa.Column("conformite_statut", sa.String(20), server_default=sa.text("'A_REGULARISER'")))
    op.add_column("drivers", sa.Column("statut", sa.String(20), server_default=sa.text("'ACTIF'")))
    op.add_column("drivers", sa.Column("photo_s3_key", sa.String(500)))
    op.add_column("drivers", sa.Column("notes", sa.Text()))
    op.add_column("drivers", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.add_column("drivers", sa.Column("created_by", sa.UUID()))
    op.add_column("drivers", sa.Column("updated_by", sa.UUID()))

    # Migrate existing data: first_name → prenom, last_name → nom, phone → telephone_mobile, hire_date → date_entree
    op.execute("""
        UPDATE drivers
        SET nom = last_name,
            prenom = first_name,
            telephone_mobile = phone,
            date_entree = hire_date
        WHERE nom IS NULL
    """)

    op.create_unique_constraint("uq_drivers_tenant_nir", "drivers", ["tenant_id", "nir"])

    # ------------------------------------------------------------------
    # 7. ALTER vehicles — add Module B fields
    # ------------------------------------------------------------------
    op.add_column("vehicles", sa.Column("immatriculation", sa.String(15)))
    op.add_column("vehicles", sa.Column("type_entity", sa.String(20), server_default=sa.text("'VEHICULE'")))
    op.add_column("vehicles", sa.Column("categorie", sa.String(30)))
    op.add_column("vehicles", sa.Column("marque", sa.String(50)))
    op.add_column("vehicles", sa.Column("modele", sa.String(50)))
    op.add_column("vehicles", sa.Column("annee_mise_en_circulation", sa.Integer()))
    op.add_column("vehicles", sa.Column("date_premiere_immatriculation", sa.Date()))
    op.add_column("vehicles", sa.Column("carrosserie", sa.String(30)))
    op.add_column("vehicles", sa.Column("ptac_kg", sa.Integer()))
    op.add_column("vehicles", sa.Column("ptra_kg", sa.Integer()))
    op.add_column("vehicles", sa.Column("charge_utile_kg", sa.Integer()))
    op.add_column("vehicles", sa.Column("volume_m3", sa.Numeric(8, 2)))
    op.add_column("vehicles", sa.Column("longueur_utile_m", sa.Numeric(5, 2)))
    op.add_column("vehicles", sa.Column("largeur_utile_m", sa.Numeric(5, 2)))
    op.add_column("vehicles", sa.Column("hauteur_utile_m", sa.Numeric(5, 2)))
    op.add_column("vehicles", sa.Column("nb_palettes_europe", sa.Integer()))
    op.add_column("vehicles", sa.Column("nb_essieux", sa.Integer()))
    op.add_column("vehicles", sa.Column("motorisation", sa.String(20)))
    op.add_column("vehicles", sa.Column("norme_euro", sa.String(10)))
    op.add_column("vehicles", sa.Column("equipements", sa.JSON()))
    op.add_column("vehicles", sa.Column("temperature_min", sa.Numeric(5, 1)))
    op.add_column("vehicles", sa.Column("temperature_max", sa.Numeric(5, 1)))
    op.add_column("vehicles", sa.Column("proprietaire", sa.String(30), server_default=sa.text("'PROPRE'")))
    op.add_column("vehicles", sa.Column("loueur_nom", sa.String(100)))
    op.add_column("vehicles", sa.Column("contrat_location_ref", sa.String(50)))
    op.add_column("vehicles", sa.Column("date_fin_contrat_location", sa.Date()))
    op.add_column("vehicles", sa.Column("km_compteur_actuel", sa.Integer()))
    op.add_column("vehicles", sa.Column("date_dernier_releve_km", sa.Date()))
    op.add_column("vehicles", sa.Column("centre_cout_id", sa.UUID()))
    op.add_column("vehicles", sa.Column("conformite_statut", sa.String(20), server_default=sa.text("'A_REGULARISER'")))
    op.add_column("vehicles", sa.Column("statut", sa.String(30), server_default=sa.text("'ACTIF'")))
    op.add_column("vehicles", sa.Column("notes", sa.Text()))
    op.add_column("vehicles", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")))
    op.add_column("vehicles", sa.Column("created_by", sa.UUID()))
    op.add_column("vehicles", sa.Column("updated_by", sa.UUID()))

    # Migrate existing data: plate_number → immatriculation, brand → marque, model → modele
    op.execute("""
        UPDATE vehicles
        SET immatriculation = plate_number,
            marque = brand,
            modele = model,
            date_premiere_immatriculation = first_registration,
            charge_utile_kg = CAST(payload_kg AS INTEGER)
        WHERE immatriculation IS NULL
    """)

    op.create_unique_constraint("uq_vehicles_tenant_immat", "vehicles", ["tenant_id", "immatriculation"])


def downgrade() -> None:
    # Drop new tables
    op.drop_table("subcontractor_contracts")
    op.drop_table("subcontractors")
    op.drop_table("client_addresses")
    op.drop_table("client_contacts")

    # Drop unique constraints
    op.drop_constraint("uq_vehicles_tenant_immat", "vehicles")
    op.drop_constraint("uq_drivers_tenant_nir", "drivers")
    op.drop_constraint("uq_customers_tenant_code", "customers")

    # Drop added columns from vehicles
    for col in [
        "immatriculation", "type_entity", "categorie", "marque", "modele",
        "annee_mise_en_circulation", "date_premiere_immatriculation", "carrosserie",
        "ptac_kg", "ptra_kg", "charge_utile_kg", "volume_m3",
        "longueur_utile_m", "largeur_utile_m", "hauteur_utile_m",
        "nb_palettes_europe", "nb_essieux", "motorisation", "norme_euro",
        "equipements", "temperature_min", "temperature_max",
        "proprietaire", "loueur_nom", "contrat_location_ref", "date_fin_contrat_location",
        "km_compteur_actuel", "date_dernier_releve_km", "centre_cout_id",
        "conformite_statut", "statut", "notes", "updated_at", "created_by", "updated_by",
    ]:
        op.drop_column("vehicles", col)

    # Drop added columns from drivers
    for col in [
        "civilite", "nom", "prenom", "date_naissance", "lieu_naissance",
        "nationalite", "nir", "adresse_ligne1", "adresse_ligne2",
        "code_postal", "ville", "pays", "telephone_mobile",
        "statut_emploi", "agence_interim_nom", "agence_interim_contact",
        "type_contrat", "date_entree", "date_sortie", "motif_sortie", "poste",
        "categorie_permis", "coefficient", "groupe",
        "salaire_base_mensuel", "taux_horaire",
        "qualification_fimo", "qualification_fco", "qualification_adr",
        "qualification_adr_classes", "carte_conducteur_numero",
        "centre_cout_id", "conformite_statut", "statut",
        "photo_s3_key", "notes", "updated_at", "created_by", "updated_by",
    ]:
        op.drop_column("drivers", col)

    # Drop added columns from customers
    for col in [
        "code", "raison_sociale", "nom_commercial", "siret", "tva_intracom", "code_naf",
        "adresse_facturation_ligne1", "adresse_facturation_ligne2",
        "adresse_facturation_cp", "adresse_facturation_ville", "adresse_facturation_pays",
        "telephone", "email", "site_web",
        "delai_paiement_jours", "mode_paiement", "condition_paiement_texte",
        "escompte_pourcent", "penalite_retard_pourcent", "indemnite_recouvrement",
        "plafond_encours", "sla_delai_livraison_heures", "sla_taux_service_pourcent",
        "sla_penalite_texte", "agency_ids", "notes", "statut",
        "date_debut_relation", "updated_at", "created_by", "updated_by",
    ]:
        op.drop_column("customers", col)
