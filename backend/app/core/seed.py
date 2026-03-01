"""Seed script — creates demo tenant, agency, roles, admin user, FR presets, Module B demo data."""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.core.security import hash_password

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000100")

# FR document types for drivers and vehicles
FR_DOC_TYPES = [
    # Driver documents
    ("driver", "permis_conduire", "Permis de conduire", None, True),
    ("driver", "fimo", "FIMO", 60, True),
    ("driver", "fco", "FCO", 60, True),
    ("driver", "visite_medicale", "Visite médicale", 24, True),
    ("driver", "carte_conducteur", "Carte conducteur", 60, True),
    ("driver", "adr", "ADR", 60, False),
    ("driver", "carte_identite", "Carte d'identité", None, False),
    # Vehicle documents
    ("vehicle", "carte_grise", "Carte grise", None, True),
    ("vehicle", "controle_technique", "Contrôle technique", 12, True),
    ("vehicle", "assurance", "Assurance", 12, True),
    ("vehicle", "attestation_capacite", "Attestation de capacité", None, True),
]

# FR payroll variable types
FR_PAYROLL_VAR_TYPES = [
    ("heures_normales", "Heures normales", "h", "temps"),
    ("heures_sup_25", "Heures sup. 25%", "h", "temps"),
    ("heures_sup_50", "Heures sup. 50%", "h", "temps"),
    ("heures_nuit", "Heures de nuit", "h", "temps"),
    ("prime_panier", "Prime de panier", "j", "prime"),
    ("prime_decouche", "Prime de découché", "j", "prime"),
    ("prime_salissure", "Prime de salissure", "j", "prime"),
    ("km_personnels", "Km personnels", "km", "frais"),
    ("indemnite_repas", "Indemnité repas", "j", "frais"),
    ("absence_maladie", "Absence maladie", "j", "absence"),
    ("absence_cp", "Absence CP", "j", "absence"),
    ("absence_rtt", "Absence RTT", "j", "absence"),
]

# Default SILAE mappings
SILAE_MAPPINGS = [
    ("heures_normales", "0100", "Heures normales"),
    ("heures_sup_25", "0110", "HS 25%"),
    ("heures_sup_50", "0120", "HS 50%"),
    ("heures_nuit", "0200", "Heures nuit"),
    ("prime_panier", "0300", "Panier"),
    ("prime_decouche", "0310", "Découché"),
    ("prime_salissure", "0320", "Salissure"),
    ("km_personnels", "0400", "IK"),
    ("indemnite_repas", "0410", "Repas"),
    ("absence_maladie", "0500", "Maladie"),
    ("absence_cp", "0510", "CP"),
    ("absence_rtt", "0520", "RTT"),
]

ROLES = [
    ("admin", ["*"]),
    ("exploitation", [
        "jobs.create", "jobs.read", "jobs.update", "jobs.assign",
        "masterdata.read", "masterdata.update",
        "documents.read", "documents.create",
        "tasks.read", "tasks.update",
    ]),
    ("compta", [
        "billing.invoice.create", "billing.invoice.read", "billing.invoice.validate",
        "billing.pricing.read", "billing.pricing.update",
        "ocr.read", "ocr.create", "ocr.validate",
        "jobs.read", "masterdata.read", "tasks.read", "tasks.update",
    ]),
    ("rh_paie", [
        "payroll.read", "payroll.import", "payroll.export", "payroll.submit", "payroll.approve",
        "documents.read", "documents.create",
        "masterdata.driver.read", "masterdata.driver.update",
        "tasks.read", "tasks.update",
    ]),
    ("lecture_seule", [
        "jobs.read", "masterdata.read", "documents.read",
        "billing.invoice.read", "billing.pricing.read",
        "payroll.read", "tasks.read",
    ]),
]

# ── Module B demo data ────────────────────────────────────────────

DEMO_CUSTOMERS = [
    {
        "code": "CLI-001", "raison_sociale": "CARREFOUR SUPPLY CHAIN", "nom_commercial": "Carrefour",
        "siret": "65201405100044", "siren": "652014051",
        "tva_intracom": "FR82652014051", "code_naf": "52.29A",
        "adresse_facturation_ligne1": "1 Avenue des Champs", "adresse_facturation_cp": "75008",
        "adresse_facturation_ville": "Paris", "adresse_facturation_pays": "FR",
        "telephone": "+33 1 60 00 00 00", "email": "transport@carrefour.test",
        "delai_paiement_jours": 30, "mode_paiement": "VIREMENT",
        "condition_paiement_texte": "30 jours nets date de facture",
        "plafond_encours": 50000, "statut": "ACTIF",
        "date_debut_relation": "2020-06-01",
    },
    {
        "code": "CLI-002", "raison_sociale": "AUCHAN RETAIL FRANCE", "nom_commercial": "Auchan",
        "siret": "41021072200017", "siren": "410210722",
        "adresse_facturation_ligne1": "200 Rue de la Recherche", "adresse_facturation_cp": "59650",
        "adresse_facturation_ville": "Villeneuve-d'Ascq", "adresse_facturation_pays": "FR",
        "telephone": "+33 3 20 67 68 69", "email": "logistique@auchan.test",
        "delai_paiement_jours": 45, "mode_paiement": "VIREMENT",
        "statut": "ACTIF",
    },
    {
        "code": "CLI-003", "raison_sociale": "LIDL FRANCE SNC",
        "siret": "34326262200892", "siren": "343262622",
        "adresse_facturation_ligne1": "35 Rue Charles Péguy", "adresse_facturation_cp": "67200",
        "adresse_facturation_ville": "Strasbourg", "adresse_facturation_pays": "FR",
        "email": "transport@lidl.test",
        "delai_paiement_jours": 30, "mode_paiement": "VIREMENT",
        "statut": "PROSPECT",
    },
]

DEMO_DRIVERS = [
    {
        "matricule": "COND-001", "civilite": "M", "nom": "DUPONT", "prenom": "Jean",
        "first_name": "Jean", "last_name": "DUPONT",
        "date_naissance": "1985-07-22", "lieu_naissance": "Lyon (69)",
        "nationalite": "FR", "nir": "185076913512345",
        "adresse_ligne1": "8 Impasse des Lilas", "code_postal": "69003", "ville": "Lyon", "pays": "FR",
        "telephone_mobile": "+33 6 12 34 56 78", "phone": "+33 6 12 34 56 78",
        "email": "jean.dupont@email.test",
        "statut_emploi": "SALARIE", "type_contrat": "CDI",
        "date_entree": "2018-09-01", "hire_date": "2018-09-01",
        "poste": "Conducteur PL longue distance",
        "categorie_permis": ["B", "C", "CE"],
        "qualification_fimo": True, "qualification_fco": True, "qualification_adr": False,
        "carte_conducteur_numero": "F1234567890123456",
        "statut": "ACTIF", "conformite_statut": "OK",
    },
    {
        "matricule": "COND-002", "civilite": "MME", "nom": "MARTIN", "prenom": "Marie",
        "first_name": "Marie", "last_name": "MARTIN",
        "date_naissance": "1990-03-15", "lieu_naissance": "Marseille (13)",
        "nationalite": "FR", "nir": "290031300212345",
        "adresse_ligne1": "12 Rue de la Paix", "code_postal": "13001", "ville": "Marseille", "pays": "FR",
        "telephone_mobile": "+33 6 98 76 54 32", "phone": "+33 6 98 76 54 32",
        "email": "marie.martin@email.test",
        "statut_emploi": "SALARIE", "type_contrat": "CDI",
        "date_entree": "2020-02-01", "hire_date": "2020-02-01",
        "poste": "Conducteur PL regional",
        "categorie_permis": ["B", "C"],
        "qualification_fimo": True, "qualification_fco": True, "qualification_adr": False,
        "statut": "ACTIF", "conformite_statut": "OK",
    },
    {
        "matricule": "COND-003", "civilite": "M", "nom": "BERNARD", "prenom": "Pierre",
        "first_name": "Pierre", "last_name": "BERNARD",
        "date_naissance": "1978-11-08", "lieu_naissance": "Toulouse (31)",
        "nationalite": "FR", "nir": "178113100512345",
        "adresse_ligne1": "5 Avenue Victor Hugo", "code_postal": "31000", "ville": "Toulouse", "pays": "FR",
        "telephone_mobile": "+33 6 55 44 33 22", "phone": "+33 6 55 44 33 22",
        "email": "pierre.bernard@email.test",
        "statut_emploi": "SALARIE", "type_contrat": "CDI",
        "date_entree": "2015-06-15", "hire_date": "2015-06-15",
        "poste": "Conducteur SPL ADR",
        "categorie_permis": ["B", "C", "CE"],
        "qualification_fimo": True, "qualification_fco": True, "qualification_adr": True,
        "qualification_adr_classes": ["3", "4.1", "8"],
        "carte_conducteur_numero": "F9876543210987654",
        "statut": "ACTIF", "conformite_statut": "OK",
    },
]

DEMO_VEHICLES = [
    {
        "plate_number": "AB-123-CD", "immatriculation": "AB-123-CD",
        "type_entity": "VEHICULE", "categorie": "PL_PLUS_19T",
        "brand": "Renault Trucks", "marque": "Renault Trucks", "model": "T480", "modele": "T480",
        "annee_mise_en_circulation": 2022,
        "date_premiere_immatriculation": "2022-03-15",
        "vin": "VF622GVA500012345",
        "carrosserie": "BACHE", "ptac_kg": 44000, "charge_utile_kg": 25000,
        "volume_m3": 90, "longueur_utile_m": 13.6, "largeur_utile_m": 2.45, "hauteur_utile_m": 2.7,
        "nb_palettes_europe": 33, "nb_essieux": 3,
        "motorisation": "DIESEL", "norme_euro": "EURO_6",
        "proprietaire": "PROPRE", "km_compteur_actuel": 185000,
        "statut": "ACTIF", "conformite_statut": "OK",
    },
    {
        "plate_number": "EF-456-GH", "immatriculation": "EF-456-GH",
        "type_entity": "VEHICULE", "categorie": "PL_3_5T_19T",
        "brand": "Mercedes-Benz", "marque": "Mercedes-Benz", "model": "Atego 1224", "modele": "Atego 1224",
        "annee_mise_en_circulation": 2021,
        "carrosserie": "FOURGON", "ptac_kg": 12000, "charge_utile_kg": 6000,
        "motorisation": "DIESEL", "norme_euro": "EURO_6",
        "proprietaire": "LOCATION_LONGUE_DUREE", "loueur_nom": "Fraikin",
        "km_compteur_actuel": 95000,
        "statut": "ACTIF", "conformite_statut": "OK",
    },
    {
        "plate_number": "IJ-789-KL", "immatriculation": "IJ-789-KL",
        "type_entity": "SEMI_REMORQUE", "categorie": "SEMI_REMORQUE",
        "brand": "Schmitz Cargobull", "marque": "Schmitz Cargobull",
        "model": "SCB S3", "modele": "SCB S3",
        "annee_mise_en_circulation": 2023,
        "carrosserie": "FRIGORIFIQUE", "ptac_kg": 34000, "charge_utile_kg": 26000,
        "temperature_min": -25, "temperature_max": 25,
        "motorisation": "DIESEL", "norme_euro": "EURO_6",
        "proprietaire": "PROPRE",
        "statut": "ACTIF", "conformite_statut": "A_REGULARISER",
    },
]

DEMO_SUBCONTRACTORS = [
    {
        "code": "ST-001", "raison_sociale": "TRANSPORTS MARTIN SARL",
        "siret": "32345678900012", "siren": "323456789",
        "adresse_ligne1": "45 Route Nationale", "code_postal": "13015", "ville": "Marseille", "pays": "FR",
        "telephone": "+33 4 91 00 00 00", "email": "contact@transports-martin.test",
        "contact_principal_nom": "Pierre MARTIN",
        "contact_principal_telephone": "+33 6 11 22 33 44",
        "contact_principal_email": "p.martin@transports-martin.test",
        "zones_geographiques": ["13", "84", "30", "34"],
        "types_vehicules_disponibles": ["PL_PLUS_19T", "SPL"],
        "specialites": ["FRIGORIFIQUE"],
        "delai_paiement_jours": 45, "mode_paiement": "VIREMENT",
        "statut": "ACTIF", "conformite_statut": "OK",
        "note_qualite": 4.2,
    },
]


async def seed(db: AsyncSession) -> None:
    # Tenant
    await db.execute(text("""
        INSERT INTO tenants (id, name, siren, address)
        VALUES (:id, :name, :siren, :address)
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(TENANT_ID), "name": "SAF Transport Demo", "siren": "123456789", "address": "1 Rue de la Logistique, 75001 Paris"})

    # Agency
    await db.execute(text("""
        INSERT INTO agencies (id, tenant_id, name, code, address)
        VALUES (:id, :tid, :name, :code, :address)
        ON CONFLICT (id) DO NOTHING
    """), {"id": str(AGENCY_ID), "tid": str(TENANT_ID), "name": "Agence Paris", "code": "PAR", "address": "1 Rue de la Logistique, 75001 Paris"})

    # Roles
    role_ids = {}
    for role_name, perms in ROLES:
        rid = uuid.uuid4()
        role_ids[role_name] = rid
        await db.execute(text("""
            INSERT INTO roles (id, tenant_id, name, permissions)
            VALUES (:id, :tid, :name, CAST(:perms AS jsonb))
            ON CONFLICT ON CONSTRAINT uq_roles_tenant_name DO UPDATE SET permissions = EXCLUDED.permissions
        """), {"id": str(rid), "tid": str(TENANT_ID), "name": role_name, "perms": json.dumps(perms)})

    # Admin user
    await db.execute(text("""
        INSERT INTO users (id, tenant_id, agency_id, email, password_hash, full_name, role_id)
        VALUES (:id, :tid, :aid, :email, :pwd, :name, :rid)
        ON CONFLICT ON CONSTRAINT uq_users_tenant_email DO UPDATE SET password_hash = EXCLUDED.password_hash
    """), {
        "id": str(ADMIN_ID), "tid": str(TENANT_ID), "aid": str(AGENCY_ID),
        "email": "admin@saf.local", "pwd": hash_password("admin"),
        "name": "Admin SAF", "rid": str(role_ids["admin"]),
    })

    # Document types
    for entity_type, code, label, validity, mandatory in FR_DOC_TYPES:
        await db.execute(text("""
            INSERT INTO document_types (id, tenant_id, entity_type, code, label, validity_months, is_mandatory)
            VALUES (:id, :tid, :etype, :code, :label, :validity, :mandatory)
            ON CONFLICT ON CONSTRAINT uq_doctypes_tenant_entity_code DO NOTHING
        """), {
            "id": str(uuid.uuid4()), "tid": str(TENANT_ID),
            "etype": entity_type, "code": code, "label": label,
            "validity": validity, "mandatory": mandatory,
        })

    # Payroll variable types
    for code, label, unit, category in FR_PAYROLL_VAR_TYPES:
        await db.execute(text("""
            INSERT INTO payroll_variable_types (id, tenant_id, code, label, unit, category)
            VALUES (:id, :tid, :code, :label, :unit, :cat)
            ON CONFLICT ON CONSTRAINT uq_payvar_types_tenant_code DO NOTHING
        """), {
            "id": str(uuid.uuid4()), "tid": str(TENANT_ID),
            "code": code, "label": label, "unit": unit, "cat": category,
        })

    # SILAE mappings
    for var_code, target_code, target_label in SILAE_MAPPINGS:
        await db.execute(text("""
            INSERT INTO payroll_mappings (id, tenant_id, variable_type_code, target_code, target_label)
            VALUES (:id, :tid, :vcode, :tcode, :tlabel)
            ON CONFLICT ON CONSTRAINT uq_paymap_tenant_varcode DO NOTHING
        """), {
            "id": str(uuid.uuid4()), "tid": str(TENANT_ID),
            "vcode": var_code, "tcode": target_code, "tlabel": target_label,
        })

    # ── Module B: Demo Customers (full fields) ────────────────────
    for cust in DEMO_CUSTOMERS:
        cid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO customers (
                id, tenant_id, name, siren, contact_name, contact_email, payment_terms_days,
                code, raison_sociale, nom_commercial, siret, tva_intracom, code_naf,
                adresse_facturation_ligne1, adresse_facturation_cp,
                adresse_facturation_ville, adresse_facturation_pays,
                telephone, email,
                delai_paiement_jours, mode_paiement, condition_paiement_texte,
                plafond_encours, statut, date_debut_relation,
                address, agency_ids
            ) VALUES (
                :id, :tid, :name, :siren, :cn, :ce, :pt,
                :code, :rs, :nc, :siret, :tva, :naf,
                :afl1, :afcp, :afville, :afpays,
                :tel, :email,
                :dpj, :mp, :cpt,
                :plafond, :statut, :ddr,
                :addr, CAST(:agency_ids AS jsonb)
            ) ON CONFLICT (id) DO NOTHING
        """), {
            "id": str(cid), "tid": str(TENANT_ID),
            "name": cust["raison_sociale"], "siren": cust.get("siren"),
            "cn": None, "ce": cust.get("email"), "pt": cust.get("delai_paiement_jours", 30),
            "code": cust["code"], "rs": cust["raison_sociale"],
            "nc": cust.get("nom_commercial"),
            "siret": cust.get("siret"), "tva": cust.get("tva_intracom"), "naf": cust.get("code_naf"),
            "afl1": cust.get("adresse_facturation_ligne1"),
            "afcp": cust.get("adresse_facturation_cp"),
            "afville": cust.get("adresse_facturation_ville"),
            "afpays": cust.get("adresse_facturation_pays", "FR"),
            "tel": cust.get("telephone"), "email": cust.get("email"),
            "dpj": cust.get("delai_paiement_jours", 30), "mp": cust.get("mode_paiement", "VIREMENT"),
            "cpt": cust.get("condition_paiement_texte"),
            "plafond": cust.get("plafond_encours"),
            "statut": cust.get("statut", "ACTIF"),
            "ddr": cust.get("date_debut_relation"),
            "addr": cust.get("adresse_facturation_ligne1"),
            "agency_ids": json.dumps([str(AGENCY_ID)]),
        })

    # ── Module B: Demo Drivers (full fields) ──────────────────────
    for drv in DEMO_DRIVERS:
        did = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO drivers (
                id, tenant_id, agency_id, matricule, first_name, last_name, hire_date,
                civilite, nom, prenom, date_naissance, lieu_naissance, nationalite, nir,
                adresse_ligne1, code_postal, ville, pays, telephone_mobile, phone, email,
                statut_emploi, type_contrat, date_entree, poste,
                categorie_permis, qualification_fimo, qualification_fco,
                qualification_adr, qualification_adr_classes,
                carte_conducteur_numero, statut, conformite_statut
            ) VALUES (
                :id, :tid, :aid, :mat, :fn, :ln, :hd,
                :civ, :nom, :prenom, :dob, :lieu, :nat, :nir,
                :al1, :cp, :ville, :pays, :tm, :ph, :em,
                :se, :tc, :de, :poste,
                CAST(:cpermis AS jsonb), :fimo, :fco,
                :adr, CAST(:adr_classes AS jsonb),
                :ccn, :statut, :conf
            ) ON CONFLICT ON CONSTRAINT uq_drivers_tenant_matricule DO NOTHING
        """), {
            "id": str(did), "tid": str(TENANT_ID), "aid": str(AGENCY_ID),
            "mat": drv["matricule"], "fn": drv["first_name"], "ln": drv["last_name"],
            "hd": drv.get("hire_date"),
            "civ": drv.get("civilite"), "nom": drv["nom"], "prenom": drv["prenom"],
            "dob": drv.get("date_naissance"), "lieu": drv.get("lieu_naissance"),
            "nat": drv.get("nationalite"), "nir": drv.get("nir"),
            "al1": drv.get("adresse_ligne1"), "cp": drv.get("code_postal"),
            "ville": drv.get("ville"), "pays": drv.get("pays", "FR"),
            "tm": drv.get("telephone_mobile"), "ph": drv.get("phone"), "em": drv.get("email"),
            "se": drv.get("statut_emploi", "SALARIE"), "tc": drv.get("type_contrat", "CDI"),
            "de": drv.get("date_entree"), "poste": drv.get("poste"),
            "cpermis": json.dumps(drv.get("categorie_permis", [])),
            "fimo": drv.get("qualification_fimo", False),
            "fco": drv.get("qualification_fco", False),
            "adr": drv.get("qualification_adr", False),
            "adr_classes": json.dumps(drv.get("qualification_adr_classes")) if drv.get("qualification_adr_classes") else None,
            "ccn": drv.get("carte_conducteur_numero"),
            "statut": drv.get("statut", "ACTIF"),
            "conf": drv.get("conformite_statut", "A_REGULARISER"),
        })

    # ── Module B: Demo Vehicles (full fields) ─────────────────────
    for veh in DEMO_VEHICLES:
        vid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO vehicles (
                id, tenant_id, agency_id, plate_number, vin, brand, model, vehicle_type,
                payload_kg, first_registration,
                immatriculation, type_entity, categorie, marque, modele,
                annee_mise_en_circulation, date_premiere_immatriculation, carrosserie,
                ptac_kg, charge_utile_kg, volume_m3,
                longueur_utile_m, largeur_utile_m, hauteur_utile_m,
                nb_palettes_europe, nb_essieux, motorisation, norme_euro,
                temperature_min, temperature_max,
                proprietaire, loueur_nom, km_compteur_actuel,
                statut, conformite_statut
            ) VALUES (
                :id, :tid, :aid, :plate, :vin, :brand, :model, :vtype,
                :payload, :reg,
                :immat, :te, :cat, :marque, :modele,
                :amc, :dpi, :carros,
                :ptac, :cu, :vol,
                :longueur, :largeur, :hauteur,
                :npe, :nbe, :motor, :euro,
                :tmin, :tmax,
                :proprio, :loueur, :km,
                :statut, :conf
            ) ON CONFLICT ON CONSTRAINT uq_vehicles_tenant_plate DO NOTHING
        """), {
            "id": str(vid), "tid": str(TENANT_ID), "aid": str(AGENCY_ID),
            "plate": veh["plate_number"], "vin": veh.get("vin"),
            "brand": veh.get("brand"), "model": veh.get("model"),
            "vtype": veh.get("categorie"),
            "payload": veh.get("charge_utile_kg"),
            "reg": veh.get("date_premiere_immatriculation"),
            "immat": veh["immatriculation"], "te": veh["type_entity"],
            "cat": veh["categorie"], "marque": veh["marque"], "modele": veh["modele"],
            "amc": veh.get("annee_mise_en_circulation"),
            "dpi": veh.get("date_premiere_immatriculation"),
            "carros": veh.get("carrosserie"),
            "ptac": veh.get("ptac_kg"), "cu": veh.get("charge_utile_kg"),
            "vol": veh.get("volume_m3"),
            "longueur": veh.get("longueur_utile_m"), "largeur": veh.get("largeur_utile_m"),
            "hauteur": veh.get("hauteur_utile_m"),
            "npe": veh.get("nb_palettes_europe"), "nbe": veh.get("nb_essieux"),
            "motor": veh.get("motorisation"), "euro": veh.get("norme_euro"),
            "tmin": veh.get("temperature_min"), "tmax": veh.get("temperature_max"),
            "proprio": veh.get("proprietaire", "PROPRE"), "loueur": veh.get("loueur_nom"),
            "km": veh.get("km_compteur_actuel"),
            "statut": veh.get("statut", "ACTIF"),
            "conf": veh.get("conformite_statut", "A_REGULARISER"),
        })

    # ── Module B: Demo Subcontractors ─────────────────────────────
    for sub in DEMO_SUBCONTRACTORS:
        sid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO subcontractors (
                id, tenant_id, code, raison_sociale, siret, siren,
                adresse_ligne1, code_postal, ville, pays,
                telephone, email,
                contact_principal_nom, contact_principal_telephone, contact_principal_email,
                zones_geographiques, types_vehicules_disponibles, specialites,
                delai_paiement_jours, mode_paiement,
                statut, conformite_statut, note_qualite,
                agency_ids
            ) VALUES (
                :id, :tid, :code, :rs, :siret, :siren,
                :al1, :cp, :ville, :pays,
                :tel, :email,
                :cpn, :cpt, :cpe,
                CAST(:zones AS jsonb), CAST(:types_veh AS jsonb), CAST(:spec AS jsonb),
                :dpj, :mp,
                :statut, :conf, :nq,
                CAST(:agency_ids AS jsonb)
            ) ON CONFLICT ON CONSTRAINT uq_subcontractors_tenant_code DO NOTHING
        """), {
            "id": str(sid), "tid": str(TENANT_ID),
            "code": sub["code"], "rs": sub["raison_sociale"],
            "siret": sub["siret"], "siren": sub.get("siren"),
            "al1": sub["adresse_ligne1"], "cp": sub["code_postal"],
            "ville": sub["ville"], "pays": sub.get("pays", "FR"),
            "tel": sub.get("telephone"), "email": sub["email"],
            "cpn": sub.get("contact_principal_nom"),
            "cpt": sub.get("contact_principal_telephone"),
            "cpe": sub.get("contact_principal_email"),
            "zones": json.dumps(sub.get("zones_geographiques")),
            "types_veh": json.dumps(sub.get("types_vehicules_disponibles")),
            "spec": json.dumps(sub.get("specialites")),
            "dpj": sub.get("delai_paiement_jours", 45), "mp": sub.get("mode_paiement", "VIREMENT"),
            "statut": sub.get("statut", "EN_COURS_VALIDATION"),
            "conf": sub.get("conformite_statut", "A_REGULARISER"),
            "nq": sub.get("note_qualite"),
            "agency_ids": json.dumps([str(AGENCY_ID)]),
        })

        # Add a demo contract for the subcontractor
        await db.execute(text("""
            INSERT INTO subcontractor_contracts (
                id, tenant_id, subcontractor_id, reference, type_prestation,
                date_debut, date_fin, tacite_reconduction, statut
            ) VALUES (
                :id, :tid, :sid, :ref, :tp,
                :dd, :df, :tr, :statut
            )
        """), {
            "id": str(uuid.uuid4()), "tid": str(TENANT_ID), "sid": str(sid),
            "ref": "CONTRAT-ST-2026-001", "tp": "LOT_COMPLET",
            "dd": "2026-01-01", "df": "2026-12-31", "tr": True, "statut": "ACTIF",
        })

    await db.commit()
    print("Seed completed successfully.")


async def main():
    async with async_session_factory() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
