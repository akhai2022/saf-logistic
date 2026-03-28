"""
Production seed script — SAF Logistique (first customer).

Initializes:
  - Tenant (SAF LOGISTIQUE)
  - 3 Agencies (SAF LOGISTIQUE HQ, SAF LOG, SAF AT)
  - 7 Roles with FR default permissions
  - Admin + operational user accounts
  - FR document types, payroll variable types, VAT rates, SILAE mappings
  - 24 real drivers from integration data
  - 25+ real vehicles from integration data
  - 4 real clients (K+N, GEODIS, DB Schenker, Central Express)

Usage:
  python -m app.core.seed_saf
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_factory
from app.core.security import hash_password
from app.core.seed import (
    FR_DOC_TYPES,
    FR_PAYROLL_VAR_TYPES,
    FR_VAT_RATES,
    SILAE_MAPPINGS,
    DEFAULT_NOTIFICATION_CONFIGS,
    ROLES,
)

# ── IDs ─────────────────────────────────────────────────────────────
# Platform super admin (can create future tenants)
PLATFORM_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PLATFORM_AGENCY_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
PLATFORM_ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000100")

# SAF Logistique (first customer)
TENANT_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
AGENCY_HQ_ID = uuid.UUID("10000000-0000-0000-0000-000000000010")
AGENCY_LOG_ID = uuid.UUID("10000000-0000-0000-0000-000000000011")
AGENCY_AT_ID = uuid.UUID("10000000-0000-0000-0000-000000000012")
ADMIN_ID = uuid.UUID("10000000-0000-0000-0000-000000000100")

DOMAIN = "saf-logistique.fr"


def _to_date(v: str | None) -> date | None:
    if v is None:
        return None
    try:
        return date.fromisoformat(v)
    except (ValueError, TypeError):
        return None


def _make_email(prenom: str, nom: str) -> str:
    """Generate email: prenom.nom@saf-logistique.fr — normalized."""
    import unicodedata
    def normalize(s: str) -> str:
        s = unicodedata.normalize("NFD", s)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return s.lower().strip().replace(" ", "-").replace("'", "")
    return f"{normalize(prenom)}.{normalize(nom)}@{DOMAIN}"


# ── Driver data (from integration spreadsheets) ─────────────────────
DRIVERS = [
    {"nom": "ABDALLAH", "prenom": "Fouad", "telephone": "06 12 70 37 47", "date_naissance": "1984-01-24",
     "adresse": "47 rue de Goussainville", "cp": "95190", "ville": "FONTENAY EN PARISIS",
     "date_entree": "2018-11-04", "entreprise": "SAF LOGISTIQUE", "site": "PAS DE FIXE",
     "nir": "173099938018708", "permis_numero": "23AW67402", "carte_conducteur": "17017820011",
     "email_perso": "", "carte_gazoil_ref": "Total Energie (P815)", "carte_gazoil_enseigne": "TOTAL ENERGIE"},
    {"nom": "ABDALLAH", "prenom": "Khaled", "telephone": "07 66 80 25 44", "date_naissance": "1987-08-01",
     "adresse": "29 Place des fleurs", "cp": "78955", "ville": "CARRIERES SOUS POISSY",
     "date_entree": None, "entreprise": "SAF LOG", "site": "PAS DE FIXE",
     "nir": "187089935255767", "permis_numero": "24AZ46239", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "ABDALLAH", "prenom": "Sofiane", "telephone": "06 58 62 65 88", "date_naissance": "1985-09-10",
     "adresse": "58 rue Jules Ferry", "cp": "78400", "ville": "CHATOU",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "GEODIS",
     "nir": "", "permis_numero": "23AL72603", "carte_conducteur": "30995100379",
     "email_perso": ""},
    {"nom": "AKLAL", "prenom": "Lahcen", "telephone": "06 58 70 93 60", "date_naissance": None,
     "adresse": "", "cp": "", "ville": "",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "GEODIS",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "BENACHOUR", "prenom": "Kamel", "telephone": "06 65 59 50 85", "date_naissance": "1981-12-08",
     "adresse": "23 rue Jules Michelet", "cp": "92700", "ville": "COLOMBES",
     "date_entree": "2021-08-03", "entreprise": "SAF LOGISTIQUE", "site": "Garonor",
     "nir": "181129935270385", "permis_numero": "20AV11795", "carte_conducteur": "140992300535",
     "email_perso": "benachourkamel31@hotmail.com"},
    {"nom": "BENALI", "prenom": "Mokhtar", "telephone": "07 53 27 92 72", "date_naissance": "1992-12-25",
     "adresse": "2 rue des Sorbiers", "cp": "92000", "ville": "NANTERRE",
     "date_entree": "2022-06-09", "entreprise": "SAF LOGISTIQUE", "site": "",
     "nir": "192129935321504", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "BENALLOU", "prenom": "Mohammed", "telephone": "06 95 24 57 09", "date_naissance": "1989-10-24",
     "adresse": "49 avenue Lucie Desnos", "cp": "78440", "ville": "GARGENVILLE",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "BETTIOUI", "prenom": "Badr", "telephone": "07 53 65 01 00", "date_naissance": "1988-09-03",
     "adresse": "201 chemin de la Bourdette", "cp": "82500", "ville": "BEAUMONT DE LOMAGNE",
     "date_entree": "1988-09-03", "entreprise": "SAF LOGISTIQUE", "site": "Garonor",
     "nir": "188099935096376", "permis_numero": "22AG59297", "carte_conducteur": "220382200332",
     "email_perso": "badr.betti@gmail.com"},
    {"nom": "BOUKZINE", "prenom": "Mouloud", "telephone": "06 44 03 84 68", "date_naissance": "1983-03-15",
     "adresse": "2 Allee des Grands Vignes", "cp": "78200", "ville": "MANTES LA JOLIE",
     "date_entree": "2023-06-02", "entreprise": "SAF LOG", "site": "Epone",
     "nir": "183039935013187", "permis_numero": "21AX12336", "carte_conducteur": "10478100085",
     "email_perso": "boukzine@live.fr"},
    {"nom": "BRILLANT", "prenom": "Eddy", "telephone": "06 58 61 50 01", "date_naissance": "1987-03-23",
     "adresse": "11 rue Emile Zola", "cp": "93150", "ville": "LE BLANC MESNIL",
     "date_entree": "2023-06-02", "entreprise": "SAF LOGISTIQUE", "site": "Garonor",
     "nir": "187039300717319", "permis_numero": "23AK39170", "carte_conducteur": "220382200332",
     "email_perso": "brillant.eddy93@gmail.com"},
    {"nom": "CHENHAOUI", "prenom": "Rachid", "telephone": "07 69 65 62 91", "date_naissance": "1974-06-12",
     "adresse": "29 avenue Division Leclerc", "cp": "78200", "ville": "MANTES LA JOLIE",
     "date_entree": "2020-01-31", "entreprise": "SAF LOGISTIQUE", "site": "Epone",
     "nir": "174069938019005", "permis_numero": "U17W73110K", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "DAHDOUD", "prenom": "Abdelhadi", "telephone": "06 59 78 18 01", "date_naissance": "1973-09-20",
     "adresse": "36 Grande Rue", "cp": "27320", "ville": "NONANCOURT",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "Epone",
     "nir": "173099938018708", "permis_numero": "22AA99828", "carte_conducteur": "170178200113",
     "email_perso": "adahdoud@yahoo.com"},
    {"nom": "DOUZI", "prenom": "Mohammed", "telephone": "06 13 52 10 34", "date_naissance": "1970-06-22",
     "adresse": "13 rue Jean Jacques Rousseau", "cp": "95150", "ville": "BLANC MESNIL",
     "date_entree": "2016-09-30", "entreprise": "SAF LOGISTIQUE", "site": "DB Schenker",
     "nir": "", "permis_numero": "LT5457790H", "carte_conducteur": "609716000",
     "email_perso": ""},
    {"nom": "DRAME", "prenom": "Abdou", "telephone": "07 06 58 86 08", "date_naissance": "1999-05-20",
     "adresse": "45 avenue du Haut Pave", "cp": "95800", "ville": "CERGY",
     "date_entree": "2025-06-20", "entreprise": "SAF LOGISTIQUE", "site": "",
     "nir": "199059933506644", "permis_numero": "24AT33392", "carte_conducteur": "",
     "email_perso": "drameabdou427@gmail.com"},
    {"nom": "EL IDRISSI", "prenom": "Rachid", "telephone": "07 61 22 11 54", "date_naissance": "1982-04-25",
     "adresse": "3 rue Sausseuse", "cp": "78200", "ville": "MANTES LA JOLIE",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "Epone",
     "nir": "18204920002012", "permis_numero": "23AG92662", "carte_conducteur": "4822034",
     "email_perso": "rachidjajamoustaine@gmail.com"},
    {"nom": "GHANDOUR", "prenom": "Abdallah", "telephone": "", "date_naissance": None,
     "adresse": "14 rue Chaillon", "cp": "92390", "ville": "VILLENEUVE LA GARENNE",
     "date_entree": "2026-01-09", "entreprise": "SAF LOGISTIQUE", "site": "",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "GOMIS", "prenom": "Yohan", "telephone": "", "date_naissance": None,
     "adresse": "", "cp": "", "ville": "",
     "date_entree": None, "entreprise": "SAF LOG", "site": "",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "KABBOUCHI", "prenom": "Jamel", "telephone": "06 46 18 04 69", "date_naissance": None,
     "adresse": "", "cp": "", "ville": "",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "Garonor",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "KARRADA", "prenom": "Youssef", "telephone": "06 70 89 55 41", "date_naissance": "1981-11-24",
     "adresse": "4 rue Victor Schoelcher", "cp": "60200", "ville": "COMPIEGNE",
     "date_entree": "2024-09-09", "entreprise": "SAF LOGISTIQUE", "site": "Compiegne",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "KONATE", "prenom": "Youssouf", "telephone": "07 67 15 41 95", "date_naissance": "1997-07-05",
     "adresse": "2 rue Aug de Maupassant", "cp": "95370", "ville": "MONTIGNY LES CORMEILLES",
     "date_entree": "2024-10-28", "entreprise": "SAF LOG", "site": "GEODIS",
     "nir": "197079517621553", "permis_numero": "24AU34337", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "MADJID", "prenom": "Abdarrahmane", "telephone": "06 35 59 65 97", "date_naissance": "1971-11-11",
     "adresse": "3 avenue de Bretagne", "cp": "95230", "ville": "SOISY SOUS MONTMORENCY",
     "date_entree": "2016-05-30", "entreprise": "SAF LOGISTIQUE", "site": "Geodis",
     "nir": "171119935299870", "permis_numero": "20AV65410", "carte_conducteur": "61195100064",
     "email_perso": ""},
    {"nom": "MAJD", "prenom": "Rachid", "telephone": "07 67 83 33 84", "date_naissance": "1974-04-06",
     "adresse": "9 rue des Closeaux", "cp": "95130", "ville": "FRANCONVILLE",
     "date_entree": "2020-03-02", "entreprise": "SAF LOGISTIQUE", "site": "GEODIS",
     "nir": "174049935070171", "permis_numero": "23AF08709", "carte_conducteur": "61195100064",
     "email_perso": "madjid.9295@gmail.com"},
    {"nom": "MENOUER", "prenom": "Sadji", "telephone": "06 73 80 75 93", "date_naissance": None,
     "adresse": "", "cp": "", "ville": "",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "Central Express",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "NIAKATE", "prenom": "Mamadou", "telephone": "06 22 66 63 48", "date_naissance": None,
     "adresse": "55 rue Michelet", "cp": "92700", "ville": "COLOMBES",
     "date_entree": None, "entreprise": "SAF LOG", "site": "",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "OULAIN", "prenom": "Mustapha", "telephone": "06 51 15 36 53", "date_naissance": "1984-08-21",
     "adresse": "4 rue Jean Anouilh", "cp": "78500", "ville": "SARTROUVILLE",
     "date_entree": "2025-11-02", "entreprise": "SAF LOG", "site": "GEODIS",
     "nir": "184089938013785", "permis_numero": "25ACA1094", "carte_conducteur": "241278401913",
     "email_perso": ""},
    {"nom": "WAMBA", "prenom": "Christian", "telephone": "06 19 77 92 36", "date_naissance": "1997-01-23",
     "adresse": "185 rue du General de Gaulle", "cp": "95100", "ville": "MONTIGNY LES CORMEILLES",
     "date_entree": "2022-09-06", "entreprise": "SAF LOG", "site": "GEODIS",
     "nir": "197017511279294", "permis_numero": "22AZ11019", "carte_conducteur": "141295300398",
     "email_perso": "wambaachristian@gmail.com"},
    {"nom": "JARI", "prenom": "Said", "telephone": "06 65 06 05 63", "date_naissance": None,
     "adresse": "", "cp": "", "ville": "",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "GEODIS",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
    {"nom": "ZIDANE", "prenom": "Mehdi", "telephone": "", "date_naissance": None,
     "adresse": "", "cp": "", "ville": "",
     "date_entree": None, "entreprise": "SAF LOGISTIQUE", "site": "",
     "nir": "", "permis_numero": "", "carte_conducteur": "",
     "email_perso": ""},
]

# ── Vehicle data (from integration spreadsheets) ─────────────────────
VEHICLES = [
    {"immat": "DX-485-WV", "marque": "MERCEDES", "modele": "", "tonnage": 11.9, "genre": "Camion", "mise_circulation": "2008-05-01", "date_entree": "2024-04-12"},
    {"immat": "ER-089-SZ", "marque": "MERCEDES", "modele": "ATEGO", "tonnage": 12.0, "genre": "Camion", "mise_circulation": "2009-03-01", "date_entree": "2024-04-12", "siren": "820904084"},
    {"immat": "EP-374-FW", "marque": "MERCEDES", "modele": "ATEGO", "tonnage": 12.0, "genre": "Camion", "mise_circulation": "2009-01-01", "date_entree": "2024-04-12", "siren": "820904084"},
    {"immat": "DL-779-DS", "marque": "MERCEDES", "modele": "SPRINTER", "tonnage": 3.5, "genre": "VU", "mise_circulation": "2014-10-01", "date_entree": "2024-04-12", "ct_date": "2028-01-28"},
    {"immat": "CS-830-NH", "marque": "MERCEDES", "modele": "", "tonnage": 10.5, "genre": "Camion", "mise_circulation": "2007-12-01", "date_entree": "2024-04-12", "assurance": "AXA"},
    {"immat": "CB-631-JN", "marque": "RENAULT", "modele": "PREMIUM", "tonnage": 19.0, "genre": "Tracteur", "mise_circulation": "2012-02-01", "date_entree": "2024-04-12", "siren": "952916229", "assurance": "AXA"},
    {"immat": "BL-336-PV", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "mise_circulation": "2006-11-01", "date_entree": "2024-04-12", "ct_date": "2026-07-01", "limiteur_date": "2026-06-19", "tachy_date": "2027-06-20", "assurance": "AXA"},
    {"immat": "BE-507-CV", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "ct_date": "2027-03-05", "limiteur_date": "2026-11-23", "tachy_date": "2027-11-21", "assurance": "AXA"},
    {"immat": "AK-768-JX", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "AXA"},
    {"immat": "AW-639-SE", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "AXA"},
    {"immat": "CH-398-HL", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "AXA"},
    {"immat": "DF-314-VL", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "ct_date": "2026-06-30", "limiteur_date": "2026-05-15", "tachy_date": "2026-05-21", "assurance": "Hermann Celikian"},
    {"immat": "CT-529-GA", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "ct_date": "2027-01-16", "limiteur_date": "2027-01-16", "tachy_date": "2028-01-16", "assurance": "AXA"},
    {"immat": "DB-670-SD", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion"},
    {"immat": "FJ-592-MB", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "Hermann Celikian"},
    {"immat": "EC-521-HX", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "Hermann Celikian"},
    {"immat": "BF-519-WT", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "ct_date": "2027-02-07", "limiteur_date": "2026-11-28", "tachy_date": "2027-11-29", "assurance": "AXA"},
    {"immat": "AC-013-YA", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "AXA"},
    {"immat": "AD-815-GW", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "ct_date": "2027-02-27", "limiteur_date": "2026-10-07", "tachy_date": "2027-01-23", "assurance": "AXA"},
    {"immat": "BF-304-TQ", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "ct_date": "2026-11-28", "limiteur_date": "2026-08-19", "tachy_date": "2027-08-20", "assurance": "Hermann Celikian"},
    {"immat": "DS-920-PV", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "Hermann Celikian"},
    {"immat": "EB-007-HK", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "Hermann Celikian"},
    {"immat": "DT-392-ED", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion"},
    {"immat": "FF-687-FS", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "MMA"},
    {"immat": "BZ-627-AM", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "Hermann Celikian"},
    {"immat": "CL-231-LX", "marque": "MERCEDES", "modele": "", "tonnage": 12.0, "genre": "Camion", "assurance": "ALLIANZ"},
]

# ── Clients ──────────────────────────────────────────────────────────
CLIENTS = [
    {"code": "KN-001", "raison_sociale": "KUEHNE + NAGEL", "nom_commercial": "Kuehne+Nagel",
     "adresse": "Zone Industrielle", "cp": "78680", "ville": "Epone", "pays": "FR",
     "email": "transport@kuehne-nagel.com", "telephone": "",
     "delai_paiement_jours": 30, "mode_paiement": "VIREMENT", "statut": "ACTIF"},
    {"code": "GEO-001", "raison_sociale": "GEODIS", "nom_commercial": "Geodis",
     "adresse": "", "cp": "", "ville": "", "pays": "FR",
     "email": "", "telephone": "",
     "delai_paiement_jours": 30, "mode_paiement": "VIREMENT", "statut": "ACTIF"},
    {"code": "DBS-001", "raison_sociale": "DB SCHENKER", "nom_commercial": "DB Schenker",
     "adresse": "", "cp": "", "ville": "", "pays": "FR",
     "email": "", "telephone": "",
     "delai_paiement_jours": 30, "mode_paiement": "VIREMENT", "statut": "ACTIF"},
    {"code": "CEX-001", "raison_sociale": "CENTRAL EXPRESS", "nom_commercial": "Central Express",
     "adresse": "", "cp": "", "ville": "", "pays": "FR",
     "email": "", "telephone": "",
     "delai_paiement_jours": 30, "mode_paiement": "VIREMENT", "statut": "ACTIF"},
]

# ── Platform users (admin + operational) ─────────────────────────────
PLATFORM_USERS = [
    ("admin@saf-logistique.fr", "SafAdmin2026!", "Administrateur SAF", "admin"),
    ("exploitation@saf-logistique.fr", "SafExploit2026!", "Service Exploitation", "exploitation"),
    ("compta@saf-logistique.fr", "SafCompta2026!", "Service Comptabilite", "compta"),
    ("rh@saf-logistique.fr", "SafRH2026!", "Service RH Paie", "rh_paie"),
    ("flotte@saf-logistique.fr", "SafFlotte2026!", "Service Flotte", "flotte"),
]


def _agency_id_for(entreprise: str) -> str:
    e = entreprise.strip().upper().replace(" ", "")
    if "SAFAT" in e:
        return str(AGENCY_AT_ID)
    elif "SAFLOG" in e and "LOGISTIQUE" not in e:
        return str(AGENCY_LOG_ID)
    return str(AGENCY_HQ_ID)


def _vehicle_category(tonnage: float, genre: str) -> str:
    if "tracteur" in genre.lower():
        return "SPL"
    if tonnage >= 19.0:
        return "PL_PLUS_19T"
    if tonnage >= 3.5:
        return "PL_3_5T_19T"
    return "VL"


async def seed_saf(db: AsyncSession) -> None:
    """Full production seed for SAF Logistique."""
    tid = str(TENANT_ID)

    # ══════════════════════════════════════════════════════════════════
    # PLATFORM SUPER ADMIN (for creating future tenants)
    # ══════════════════════════════════════════════════════════════════
    ptid = str(PLATFORM_TENANT_ID)
    await db.execute(text("""
        INSERT INTO tenants (id, name, siren, address)
        VALUES (:id, :name, :siren, :address)
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    """), {"id": ptid, "name": "Plateforme SAF", "siren": "", "address": ""})

    await db.execute(text("""
        INSERT INTO agencies (id, tenant_id, name, code)
        VALUES (:id, :tid, :name, :code)
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
    """), {"id": str(PLATFORM_AGENCY_ID), "tid": ptid, "name": "Administration", "code": "ADMIN"})

    # Create platform admin role
    platform_role_id = uuid.uuid4()
    await db.execute(text("""
        INSERT INTO roles (id, tenant_id, name, permissions)
        VALUES (:id, :tid, :name, CAST(:perms AS jsonb))
        ON CONFLICT ON CONSTRAINT uq_roles_tenant_name DO UPDATE SET permissions = EXCLUDED.permissions
        RETURNING id
    """), {"id": str(platform_role_id), "tid": ptid, "name": "admin", "perms": json.dumps(["*"])})
    platform_role_id = str(platform_role_id)

    await db.execute(text("""
        INSERT INTO users (id, tenant_id, agency_id, email, password_hash, full_name, role_id, is_super_admin)
        VALUES (:id, :tid, :aid, :email, :pwd, :name, :rid, true)
        ON CONFLICT ON CONSTRAINT uq_users_tenant_email DO UPDATE
            SET password_hash = EXCLUDED.password_hash, is_super_admin = true
    """), {
        "id": str(PLATFORM_ADMIN_ID), "tid": ptid, "aid": str(PLATFORM_AGENCY_ID),
        "email": "admin@dataforgeai.fr", "pwd": hash_password("DataForge2026!"),
        "name": "Super Admin Plateforme", "rid": platform_role_id,
    })

    # ══════════════════════════════════════════════════════════════════
    # SAF LOGISTIQUE (first customer)
    # ══════════════════════════════════════════════════════════════════

    # ── 1. Tenant ────────────────────────────────────────────────────
    await db.execute(text("""
        INSERT INTO tenants (id, name, siren, address)
        VALUES (:id, :name, :siren, :address)
        ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, siren = EXCLUDED.siren, address = EXCLUDED.address
    """), {"id": tid, "name": "SAF LOGISTIQUE", "siren": "820904084", "address": "Fontenay-en-Parisis, 95190"})

    # ── 2. Agencies ──────────────────────────────────────────────────
    for aid, name, code in [
        (AGENCY_HQ_ID, "SAF LOGISTIQUE", "HQ"),
        (AGENCY_LOG_ID, "SAF LOG", "LOG"),
        (AGENCY_AT_ID, "SAF AT", "AT"),
    ]:
        await db.execute(text("""
            INSERT INTO agencies (id, tenant_id, name, code)
            VALUES (:id, :tid, :name, :code)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code = EXCLUDED.code
        """), {"id": str(aid), "tid": tid, "name": name, "code": code})

    # ── 3. Roles ─────────────────────────────────────────────────────
    role_ids: dict[str, str] = {}
    for role_name, perms in ROLES:
        rid = uuid.uuid4()
        result = await db.execute(text("""
            INSERT INTO roles (id, tenant_id, name, permissions)
            VALUES (:id, :tid, :name, CAST(:perms AS jsonb))
            ON CONFLICT ON CONSTRAINT uq_roles_tenant_name DO UPDATE SET permissions = EXCLUDED.permissions
            RETURNING id
        """), {"id": str(rid), "tid": tid, "name": role_name, "perms": json.dumps(perms)})
        role_ids[role_name] = str(result.scalar())

    # ── 4. Admin user (super admin) ──────────────────────────────────
    await db.execute(text("""
        INSERT INTO users (id, tenant_id, agency_id, email, password_hash, full_name, role_id, is_super_admin)
        VALUES (:id, :tid, :aid, :email, :pwd, :name, :rid, true)
        ON CONFLICT ON CONSTRAINT uq_users_tenant_email DO UPDATE
            SET password_hash = EXCLUDED.password_hash, is_super_admin = true
    """), {
        "id": str(ADMIN_ID), "tid": tid, "aid": str(AGENCY_HQ_ID),
        "email": "admin@saf-logistique.fr", "pwd": hash_password("SafAdmin2026!"),
        "name": "Administrateur SAF", "rid": role_ids["admin"],
    })

    # ── 5. Operational users ─────────────────────────────────────────
    for email, password, full_name, role_key in PLATFORM_USERS:
        if email == "admin@saf-logistique.fr":
            continue  # already created above
        uid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO users (id, tenant_id, agency_id, email, password_hash, full_name, role_id)
            VALUES (:id, :tid, :aid, :email, :pwd, :name, :rid)
            ON CONFLICT ON CONSTRAINT uq_users_tenant_email DO UPDATE
                SET password_hash = EXCLUDED.password_hash, full_name = EXCLUDED.full_name, role_id = EXCLUDED.role_id
        """), {
            "id": str(uid), "tid": tid, "aid": str(AGENCY_HQ_ID),
            "email": email, "pwd": hash_password(password),
            "name": full_name, "rid": role_ids[role_key],
        })

    # ── 6. FR Document types ─────────────────────────────────────────
    for entity_type, code, label, validity_months, mandatory in FR_DOC_TYPES:
        did = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO document_types (id, tenant_id, entity_type, code, label, validity_months, is_mandatory)
            VALUES (:id, :tid, :et, :code, :label, :vm, :mand)
            ON CONFLICT ON CONSTRAINT uq_doctypes_tenant_entity_code DO UPDATE SET label = EXCLUDED.label
        """), {"id": str(did), "tid": tid, "et": entity_type, "code": code,
               "label": label, "vm": validity_months, "mand": mandatory})

    # ── 7. FR Payroll variable types ─────────────────────────────────
    for code, label, unit, category in FR_PAYROLL_VAR_TYPES:
        pid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO payroll_variable_types (id, tenant_id, code, label, unit, category)
            VALUES (:id, :tid, :code, :label, :unit, :cat)
            ON CONFLICT ON CONSTRAINT uq_payvar_types_tenant_code DO UPDATE SET label = EXCLUDED.label
        """), {"id": str(pid), "tid": tid, "code": code, "label": label, "unit": unit, "cat": category})

    # ── 8. SILAE mappings ────────────────────────────────────────────
    for var_code, silae_code, silae_label in SILAE_MAPPINGS:
        sid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO payroll_mappings (id, tenant_id, variable_type_code, target_code, target_label)
            VALUES (:id, :tid, :vc, :sc, :sl)
            ON CONFLICT ON CONSTRAINT uq_paymap_tenant_varcode DO UPDATE SET target_code = EXCLUDED.target_code
        """), {"id": str(sid), "tid": tid, "vc": var_code, "sc": silae_code, "sl": silae_label})

    # ── 9. FR VAT rates ──────────────────────────────────────────────
    for rate, label, mention, is_default in FR_VAT_RATES:
        vid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO vat_configs (id, tenant_id, rate, label, mention_legale, is_default)
            VALUES (:id, :tid, :rate, :label, :mention, :def)
            ON CONFLICT DO NOTHING
        """), {"id": str(vid), "tid": tid, "rate": rate, "label": label,
               "mention": mention, "def": is_default})

    # ── 10. Notification configs ─────────────────────────────────────
    for event_type, channels, roles_list in DEFAULT_NOTIFICATION_CONFIGS:
        nid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO notification_configs (id, tenant_id, event_type, channels, recipients)
            VALUES (:id, :tid, :et, :ch, :rr)
            ON CONFLICT DO NOTHING
        """), {"id": str(nid), "tid": tid, "et": event_type,
               "ch": channels, "rr": roles_list})

    # ── 11. Company settings ───────────────────────────────────────
    await db.execute(text("""
        INSERT INTO company_settings (id, tenant_id, raison_sociale, siren, siret, tva_intracom,
            adresse_ligne1, code_postal, ville, pays, telephone, email, licence_transport)
        VALUES (:id, :tid, :rs, :siren, :siret, :tva,
            :addr, :cp, :ville, :pays, :tel, :email, :lic)
        ON CONFLICT ON CONSTRAINT uq_company_settings_tenant DO UPDATE
            SET raison_sociale = EXCLUDED.raison_sociale, siren = EXCLUDED.siren
    """), {
        "id": str(uuid.uuid4()), "tid": tid,
        "rs": "SAF LOGISTIQUE", "siren": "820904084", "siret": "82090408400015",
        "tva": "FR12820904084",
        "addr": "Zone Industrielle", "cp": "95190", "ville": "Fontenay-en-Parisis", "pays": "FR",
        "tel": "", "email": "contact@saf-logistique.fr",
        "lic": "",
    })

    # ── 12. Bank account ─────────────────────────────────────────────
    await db.execute(text("""
        INSERT INTO bank_accounts (id, tenant_id, label, iban, bic, bank_name, is_default)
        VALUES (:id, :tid, :label, :iban, :bic, :bank, true)
        ON CONFLICT DO NOTHING
    """), {
        "id": str(uuid.uuid4()), "tid": tid,
        "label": "Compte principal SAF", "iban": "FR7630003000700000000000000",
        "bic": "SOGEFRPP", "bank": "Societe Generale",
    })

    # ── 13. Compliance templates (from FR doc types) ─────────────────
    order = 1
    for entity_type, code, label, validity_months, mandatory in FR_DOC_TYPES:
        ctid = uuid.uuid4()
        validity_days = (validity_months * 30) if validity_months else None
        await db.execute(text("""
            INSERT INTO compliance_templates (id, tenant_id, entity_type, type_document,
                libelle, obligatoire, bloquant, duree_validite_defaut_jours,
                alertes_jours, ordre_affichage)
            VALUES (:id, :tid, :et, :td, :label, :oblig, :bloq, :duree, :alertes, :ordre)
            ON CONFLICT DO NOTHING
        """), {
            "id": str(ctid), "tid": tid, "et": entity_type.upper(), "td": code,
            "label": label, "oblig": mandatory, "bloq": mandatory,
            "duree": validity_days,
            "alertes": [90, 60, 30, 15] if mandatory else [60, 30],
            "ordre": order,
        })
        order += 1

    # ── 14. Pricing rules (one per client) ───────────────────────────
    # Get customer IDs
    cust_rows = (await db.execute(text(
        "SELECT id, code FROM customers WHERE tenant_id = :tid"
    ), {"tid": tid})).all()
    for crow in cust_rows:
        prid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO pricing_rules (id, tenant_id, customer_id, label, rule_type, rate, is_active)
            VALUES (:id, :tid, :cid, :label, :type, :rate, true)
            ON CONFLICT DO NOTHING
        """), {
            "id": str(prid), "tid": tid, "cid": str(crow.id),
            "label": f"Tarif standard - {crow.code}", "type": "km", "rate": 1.85,
        })

    # ── 15. Drivers ──────────────────────────────────────────────────
    matricule_counter = 1
    for d in DRIVERS:
        did = uuid.uuid4()
        matricule = f"SAF-{matricule_counter:03d}"
        matricule_counter += 1
        agency_id = _agency_id_for(d["entreprise"])

        await db.execute(text("""
            INSERT INTO drivers (
                id, tenant_id, agency_id, matricule, nom, prenom, first_name, last_name,
                telephone_mobile, phone, email, email_personnel,
                date_naissance, adresse_ligne1, code_postal, ville, pays,
                nir, date_entree, hire_date, permis_numero,
                statut_emploi, type_contrat, statut, conformite_statut,
                categorie_permis, qualification_fimo, qualification_fco,
                carte_conducteur_numero, site_affectation,
                carte_gazoil_ref, carte_gazoil_enseigne
            ) VALUES (
                :id, :tid, :aid, :mat, :nom, :prenom, :fn, :ln,
                :tel, :tel2, :email, :email_perso,
                :dob, :addr, :cp, :ville, :pays,
                :nir, :entry, :hire, :permis_num,
                :emp, :contrat, :statut, :conf,
                CAST(:permis AS jsonb), :fimo, :fco,
                :carte, :site,
                :gazoil_ref, :gazoil_enseigne
            ) ON CONFLICT DO NOTHING
        """), {
            "id": str(did), "tid": tid, "aid": agency_id,
            "mat": matricule, "nom": d["nom"], "prenom": d["prenom"],
            "fn": d["prenom"], "ln": d["nom"],
            "tel": d["telephone"].replace(" ", ""), "tel2": d["telephone"].replace(" ", ""),
            "email": _make_email(d["prenom"], d["nom"]),
            "email_perso": d.get("email_perso") or None,
            "dob": _to_date(d["date_naissance"]),
            "addr": d["adresse"], "cp": d["cp"], "ville": d["ville"], "pays": "FR",
            "nir": d["nir"] or None, "entry": _to_date(d["date_entree"]), "hire": _to_date(d["date_entree"]),
            "permis_num": d["permis_numero"] or None,
            "emp": "SALARIE", "contrat": "CDI", "statut": "ACTIF", "conf": "A_VERIFIER",
            "permis": json.dumps(["B", "C"]),
            "fimo": True, "fco": True,
            "carte": d["carte_conducteur"] or None,
            "site": d["site"] or None,
            "gazoil_ref": d.get("carte_gazoil_ref") or None,
            "gazoil_enseigne": d.get("carte_gazoil_enseigne") or None,
        })

    # ── 12. Vehicles ─────────────────────────────────────────────────
    for v in VEHICLES:
        vid = uuid.uuid4()
        cat = _vehicle_category(v["tonnage"], v["genre"])
        ptac = int(v["tonnage"] * 1000) if v["tonnage"] else 0

        await db.execute(text("""
            INSERT INTO vehicles (
                id, tenant_id, plate_number, immatriculation,
                type_entity, categorie, brand, marque, model, modele,
                ptac_kg, motorisation, norme_euro, proprietaire,
                date_premiere_immatriculation, date_entree_flotte,
                siren_proprietaire, assurance_compagnie,
                controle_technique_date, limiteur_vitesse_date, tachygraphe_date,
                presence_matiere_dangereuse,
                statut, conformite_statut
            ) VALUES (
                :id, :tid, :plate, :immat,
                :type, :cat, :brand, :marque, :model, :modele,
                :ptac, :motor, :euro, :prop,
                :date_immat, :date_entree,
                :siren, :assurance,
                :ct_date, :limiteur_date, :tachy_date,
                :adr,
                :statut, :conf
            ) ON CONFLICT DO NOTHING
        """), {
            "id": str(vid), "tid": tid,
            "plate": v["immat"], "immat": v["immat"],
            "type": "VEHICULE", "cat": cat,
            "brand": v["marque"], "marque": v["marque"],
            "model": v["modele"] or v["marque"], "modele": v["modele"] or v["marque"],
            "ptac": ptac, "motor": "DIESEL", "euro": "EURO_5",
            "prop": "PROPRE",
            "date_immat": _to_date(v.get("mise_circulation")),
            "date_entree": _to_date(v.get("date_entree")),
            "siren": v.get("siren") or "820904084",
            "assurance": v.get("assurance") or None,
            "ct_date": _to_date(v.get("ct_date")),
            "limiteur_date": _to_date(v.get("limiteur_date")),
            "tachy_date": _to_date(v.get("tachy_date")),
            "adr": v.get("adr", False),
            "statut": "ACTIF", "conf": "A_VERIFIER",
        })

    # ── 13. Clients ──────────────────────────────────────────────────
    for c in CLIENTS:
        cid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO customers (
                id, tenant_id, name, code, raison_sociale, nom_commercial,
                adresse_facturation_ligne1, adresse_facturation_cp,
                adresse_facturation_ville, adresse_facturation_pays,
                email, telephone,
                delai_paiement_jours, mode_paiement, statut
            ) VALUES (
                :id, :tid, :name, :code, :rs, :nc,
                :addr, :cp, :ville, :pays,
                :email, :tel,
                :delai, :mode, :statut
            ) ON CONFLICT DO NOTHING
        """), {
            "id": str(cid), "tid": tid, "name": c["raison_sociale"], "code": c["code"],
            "rs": c["raison_sociale"], "nc": c["nom_commercial"],
            "addr": c["adresse"], "cp": c["cp"], "ville": c["ville"], "pays": c["pays"],
            "email": c["email"], "tel": c["telephone"],
            "delai": c["delai_paiement_jours"], "mode": c["mode_paiement"],
            "statut": c["statut"],
        })

    # ── 16. Route Templates (tournées modèles) from SAF planning data
    ROUTE_TEMPLATES = [
        {"code": "1029", "label": "Tournee 1029 — K+N Epone", "client_code": "KN-001", "site": "Epone", "recurrence": "LUN_VEN"},
        {"code": "1013", "label": "Tournee 1013 — K+N Epone", "client_code": "KN-001", "site": "Epone", "recurrence": "LUN_VEN"},
        {"code": "1016", "label": "Tournee 1016 — K+N Epone", "client_code": "KN-001", "site": "Epone", "recurrence": "LUN_VEN"},
        {"code": "1017", "label": "Tournee 1017 — K+N Epone", "client_code": "KN-001", "site": "Epone", "recurrence": "LUN_VEN"},
        {"code": "1012", "label": "Tournee 1012 — K+N Epone", "client_code": "KN-001", "site": "Epone", "recurrence": "LUN_VEN"},
        {"code": "095174", "label": "Tournee 95174 — Geodis", "client_code": "GEO-001", "site": "Geodis", "recurrence": "LUN_VEN"},
        {"code": "095237", "label": "Tournee 95237 — Geodis", "client_code": "GEO-001", "site": "Geodis", "recurrence": "LUN_VEN"},
        {"code": "095238", "label": "Tournee 95238 — Geodis", "client_code": "GEO-001", "site": "Geodis", "recurrence": "LUN_VEN"},
        {"code": "174", "label": "Tournee 174 — Geodis", "client_code": "GEO-001", "site": "Geodis", "recurrence": "LUN_VEN"},
        {"code": "1406", "label": "Tournee 1406 — K+N Epone", "client_code": "KN-001", "site": "Epone", "recurrence": "LUN_VEN"},
    ]
    ROUTES = ROUTE_TEMPLATES  # alias for legacy seed below
    # Build customer code→id lookup
    cust_lookup = {}
    for crow in (await db.execute(text("SELECT id, code FROM customers WHERE tenant_id = :tid"), {"tid": tid})).fetchall():
        cust_lookup[crow.code] = str(crow.id)

    # Legacy routes table (kept for backward compat)
    for rt in ROUTES:
        rtid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO routes (id, tenant_id, numero, libelle, client_id, site, recurrence,
                date_debut, type_mission, statut)
            VALUES (:id, :tid, :num, :lib, :cid, :site, :rec, :debut, :type, 'ACTIF')
            ON CONFLICT ON CONSTRAINT uq_routes_tenant_numero DO NOTHING
        """), {
            "id": str(rtid), "tid": tid, "num": rt["code"], "lib": rt["label"],
            "cid": cust_lookup.get(rt["client_code"]),
            "site": rt["site"], "rec": rt["recurrence"],
            "debut": date(2025, 12, 1), "type": "LOT_COMPLET",
        })

    # New route_templates table
    for rt in ROUTE_TEMPLATES:
        rtid = uuid.uuid4()
        await db.execute(text("""
            INSERT INTO route_templates (id, tenant_id, code, label, customer_id, site,
                recurrence_rule, valid_from, default_mission_type, status)
            VALUES (:id, :tid, :code, :label, :cid, :site, :rec, :debut, :type, 'ACTIVE')
            ON CONFLICT ON CONSTRAINT uq_route_templates_tenant_code DO NOTHING
        """), {
            "id": str(rtid), "tid": tid, "code": rt["code"], "label": rt["label"],
            "cid": cust_lookup.get(rt["client_code"]),
            "site": rt["site"], "rec": rt["recurrence"],
            "debut": date(2025, 12, 1), "type": "LOT_COMPLET",
        })

    await db.commit()
    print("=" * 60)
    print("SAF Logistique production seed completed successfully.")
    print("=" * 60)
    print()
    print("PLATFORM SUPER ADMIN (for managing tenants):")
    print(f"  Tenant ID: {PLATFORM_TENANT_ID}")
    print(f"  Email:     admin@dataforgeai.fr")
    print(f"  Password:  DataForge2026!")
    print()
    print("SAF LOGISTIQUE (first customer):")
    print(f"  Tenant ID: {TENANT_ID}")
    print(f"  Drivers:   {len(DRIVERS)}")
    print(f"  Vehicles:  {len(VEHICLES)}")
    print(f"  Clients:   {len(CLIENTS)}")
    print(f"  Users:     {len(PLATFORM_USERS)}")
    print()
    print("SAF user accounts:")
    for email, pwd, name, role in PLATFORM_USERS:
        print(f"  {email:40s} {pwd:20s} ({role})")
    print()


async def main() -> None:
    async with async_session_factory() as db:
        await seed_saf(db)


if __name__ == "__main__":
    asyncio.run(main())
