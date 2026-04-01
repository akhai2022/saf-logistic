#!/usr/bin/env python3
"""
Comprehensive data loader for SAF Logistic production.
Updates vehicles with registration cert data, uploads new documents (KBIS, insurance memos, certs),
creates missing vehicles, and updates driver qualification flags.

Usage:
  python integration/load_all_data.py
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

API = "https://api-saf.dataforgeai.fr"
SAF_TENANT = "10000000-0000-0000-0000-000000000001"
BASE = os.path.dirname(os.path.abspath(__file__))

# ── Vehicle updates from registration certificates ──
# Extracted from "certificat d'immatriculation20260309_15380108.pdf" (14 pages)
VEHICLE_REGISTRATION_DATA = [
    {"immat": "EC-521-HX", "marque": "DAF", "modele": "XF 460 FT", "vin": "XLRTEH4300G109904",
     "ptac_kg": 19000, "carrosserie": None, "nb_essieux": 5, "norme_euro": "EURO_6",
     "date_premiere_immatriculation": "2016-05-23", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "FF-687-FS", "marque": "MAN", "modele": "TGX", "vin": None,  # WMAA06XZZ2KM828610 from cert (18 chars — OCR error)
     "ptac_kg": 19000, "carrosserie": None, "nb_essieux": None, "norme_euro": "EURO_6",
     "date_premiere_immatriculation": "2019-04-05",
     "proprietaire": "CREDIT_BAIL", "loueur_nom": "CREDIT MUTUEL LEASING", "nombre_places": 2},
    {"immat": "DT-392-ED", "marque": "RENAULT", "modele": "D", "vin": "VF6401568FB002556",
     "ptac_kg": 12000, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_6",
     "date_premiere_immatriculation": "2015-07-09",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "EB-007-HK", "marque": "RENAULT", "modele": "D", "vin": "VF6401560GB003721",
     "ptac_kg": 12000, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_6",
     "date_premiere_immatriculation": "2016-04-14", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "DX-485-WV", "marque": "MERCEDES", "modele": "ATEGO", "vin": "WDB9700581L322912",
     "ptac_kg": 11990, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2008-05-30", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "CT-529-GA", "marque": "MERCEDES", "modele": "ATEGO", "vin": "WDB9700068L139285",
     "ptac_kg": 13500, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2006-08-01", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "CB-631-JN", "marque": "RENAULT", "modele": "PREMIUM", "vin": "VF624GPA000053714",
     "ptac_kg": 19000, "carrosserie": None, "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2012-02-13",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "CH-398-HL", "marque": "RENAULT", "modele": "MIDLUM", "vin": "VF644AHL000007408",
     "ptac_kg": 16000, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2012-07-04", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "BL-336-PV", "marque": "MERCEDES", "modele": "ATEGO", "vin": "WDB9702551L150202",
     "ptac_kg": 11990, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2006-11-06", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE"},
    {"immat": "BF-304-TQ", "marque": "MERCEDES BENZ", "modele": "ATEGO", "vin": "WDB9702371L526095",
     "ptac_kg": 9500, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2011-01-05", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "AW-639-SE", "marque": "MERCEDES-BENZ", "modele": "ATEGO", "vin": "WDB9702581L488414",
     "ptac_kg": 11990, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2010-07-12", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "AK-768-JX", "marque": "MERCEDES BENZ", "modele": "ATEGO", "vin": "WDB9702581L448664",
     "ptac_kg": 11990, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2010-01-25", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "AD-815-GW", "marque": "MERCEDES", "modele": "ATEGO", "vin": "WDB9702581L406831",
     "ptac_kg": 11990, "carrosserie": "FOURGON", "nb_essieux": None, "norme_euro": "EURO_5",
     "date_premiere_immatriculation": "2009-10-08", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
    {"immat": "AC-013-YA", "marque": "MAN", "modele": "TGX", "vin": None,  # WMAA06XZZ2X9123777 from cert (18 chars — OCR error)
     "ptac_kg": 19000, "carrosserie": None, "nb_essieux": None, "norme_euro": "EURO_6",
     "date_premiere_immatriculation": "2009-05-03", "siren_proprietaire": "820904084",
     "proprietaire": "PROPRE", "nombre_places": 2},
]

# ── Insurance data from AXA memos ──
# All under AXA France IARD (F943), contract 0000011394791804, souscripteur SAS SAF LOG
INSURANCE_DATA = {
    "FJ-592-MB": {"marque": "MAN", "modele": "TGX", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2026-02-12"},
    "FF-687-FS": {"marque": "MAN", "modele": "TGX", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-11-13"},
    "EC-521-HX": {"marque": "DAF", "modele": "XF 460 FT", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-11-13"},
    "BZ-627-AM": {"marque": "IVECO", "modele": "ML 120E22P", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-11-13"},
    "DT-392-ED": {"marque": "RENAULT", "modele": "D", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-10-28"},
    "DF-314-VL": {"marque": "MAN", "modele": "TGX", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-10-20"},
    "DA-483-GL": {"marque": "RENAULT", "modele": "PREMIUM", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-10-20"},
    "AK-768-JX": {"marque": "MERCEDES BENZ", "modele": "ATEGO", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-10-20"},
    "DS-920-PV": {"marque": "RENAULT", "modele": "D", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-10-20"},
    "EB-007-HK": {"marque": "RENAULT", "modele": "D", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-10-20"},
    "CH-398-HL": {"marque": "RENAULT", "modele": "MIDLUM", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
    "AD-815-GW": {"marque": "MERCEDES", "modele": "ATEGO", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
    "CT-529-GA": {"marque": "MERCEDES", "modele": "ATEGO", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
    "BF-304-TQ": {"marque": "MERCEDES BENZ", "modele": "ATEGO", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
    "AW-639-SE": {"marque": "MERCEDES BENZ", "modele": "ATEGO", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
    "AC-013-YA": {"marque": "MAN", "modele": "TGX", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
    "BE-507-CV": {"marque": "MERCEDES BENZ", "modele": "ATEGO", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
    "BF-519-WT": {"marque": "MERCEDES BENZ", "modele": "ATEGO", "assurance_compagnie": "AXA", "assurance_numero_police": "0000011394791804", "date_entree_flotte": "2025-09-01"},
}

# ── Page mapping: which page of multi-page PDF corresponds to which vehicle ──
# Insurance memo: 2 pages per vehicle (memo + contacts)
MEMO_PAGE_MAP = [
    (1, "FJ-592-MB"), (3, "FF-687-FS"), (5, "EC-521-HX"), (7, "BZ-627-AM"),
    (9, "DT-392-ED"), (11, "DF-314-VL"), (13, "DA-483-GL"), (15, "AK-768-JX"),
    (17, "DS-920-PV"), (19, "EB-007-HK"), (21, "CH-398-HL"), (23, "AD-815-GW"),
    (25, "CT-529-GA"), (27, "BF-304-TQ"), (29, "AW-639-SE"), (31, "AC-013-YA"),
    (33, "BE-507-CV"), (35, "BF-519-WT"),
]

# Registration cert: 1 page per vehicle
CERT_PAGE_MAP = [
    (1, "EC-521-HX"), (2, "FF-687-FS"), (3, "DT-392-ED"), (4, "EB-007-HK"),
    (5, "DX-485-WV"), (6, "CT-529-GA"), (7, "CB-631-JN"), (8, "CH-398-HL"),
    (9, "BL-336-PV"), (10, "BF-304-TQ"), (11, "AW-639-SE"), (12, "AK-768-JX"),
    (13, "AD-815-GW"), (14, "AC-013-YA"),
]

# ── Driver qualification flags based on existing docs ──
# Drivers who have FIMO/FCO/ADR documents uploaded should have flags set
DRIVER_QUALIFICATIONS = {
    "ABDALLAH Fouad":    {"fimo": True, "adr": True},
    "ABDALLAH Sofiane":  {"fimo": True},
    "BENACHOUR Kamel":   {"fimo": True, "adr": True},
    "BENALI Mokhtar":    {},
    "BENALLOU Mohammed": {"fimo": True},
    "BETTIOUI Badr":     {"fimo": True, "adr": True},
    "BOUKZINE Mouloud":  {"fimo": True},
    "BRILLANT Eddy":     {"fimo": True, "adr": True},
    "DOUZI Mohammed":    {"fimo": True, "adr": True},
    "DRAME Abdou":       {"fimo": True},
    "EL IDRISSI Rachid": {"fimo": True, "adr": True},
    "GHANDOUR Abdallah": {"adr": True},
    "GOMIS Yohan":       {"fimo": True},
    "KARRADA Youssef":   {"fimo": True},
    "KONATE Youssouf":   {"fimo": True, "adr": True},
    "MADJID Abdarrahmane": {"fimo": True, "adr": True},
    "MAJD Rachid":       {"fimo": True},
    "OULAIN Mustapha":   {"fimo": True},
    "WAMBA Christian":   {"fimo": True, "adr": True},
}


def login():
    data = json.dumps({"email": "admin@saf-logistique.fr", "password": "SafAdmin2026!", "tenant_id": SAF_TENANT}).encode()
    req = urllib.request.Request(f"{API}/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode())["access_token"]


def api_get(token, path):
    req = urllib.request.Request(f"{API}{path}", headers={
        "Authorization": f"Bearer {token}", "X-Tenant-ID": SAF_TENANT})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())


class _RedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow redirects for PUT/POST (urllib defaults don't)."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        m = req.get_method()
        if code in (301, 302, 303, 307, 308) and m in ("PUT", "POST"):
            new = urllib.request.Request(
                newurl, data=req.data, method=m,
                headers={k: v for k, v in req.header_items() if k.lower() != "host"})
            return new
        return super().redirect_request(req, fp, code, msg, headers, newurl)

_opener = urllib.request.build_opener(_RedirectHandler)


def api_put(token, path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{API}{path}", data=data, method="PUT", headers={
        "Authorization": f"Bearer {token}", "X-Tenant-ID": SAF_TENANT, "Content-Type": "application/json"})
    resp = _opener.open(req, timeout=30)
    return json.loads(resp.read().decode())


def api_post(token, path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{API}{path}", data=data, method="POST", headers={
        "Authorization": f"Bearer {token}", "X-Tenant-ID": SAF_TENANT, "Content-Type": "application/json"})
    resp = _opener.open(req, timeout=30)
    return json.loads(resp.read().decode())


def split_pdf_page(pdf_path, page_num, out_path):
    """Extract a single page from a PDF using pdfseparate."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "page-%d.pdf")
        subprocess.run(["pdfseparate", pdf_path, pattern], check=True, capture_output=True)
        src = os.path.join(tmpdir, f"page-{page_num}.pdf")
        if os.path.exists(src):
            subprocess.run(["cp", src, out_path], check=True)
            return True
    return False


def extract_pdf_pages(pdf_path, start_page, end_page, out_path):
    """Extract a range of pages from a PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        pattern = os.path.join(tmpdir, "page-%d.pdf")
        subprocess.run(["pdfseparate", pdf_path, pattern], check=True, capture_output=True)
        pages = []
        for p in range(start_page, end_page + 1):
            src = os.path.join(tmpdir, f"page-{p}.pdf")
            if os.path.exists(src):
                pages.append(src)
        if pages:
            if len(pages) == 1:
                subprocess.run(["cp", pages[0], out_path], check=True)
            else:
                subprocess.run(["pdfunite"] + pages + [out_path], check=True, capture_output=True)
            return True
    return False


def upload_file_and_create_doc(token, entity_type, entity_id, doc_type, file_path, metadata):
    """Upload a file to S3 via presigned URL and create a document record."""
    hdrs = {"Authorization": f"Bearer {token}", "X-Tenant-ID": SAF_TENANT, "Content-Type": "application/json"}
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    mime = "application/pdf"

    # Step 1: Presign
    presign_data = json.dumps({"file_name": file_name, "content_type": mime, "entity_type": "document", "entity_id": entity_id}).encode()
    req = urllib.request.Request(f"{API}/v1/files/presign-upload", data=presign_data, headers=hdrs)
    resp = urllib.request.urlopen(req, timeout=15)
    presign = json.loads(resp.read().decode())
    s3_key = presign["s3_key"]
    upload_url = presign["upload_url"]

    # Step 2: Upload to S3
    with open(file_path, "rb") as f:
        file_data = f.read()
    req = urllib.request.Request(upload_url, data=file_data, method="PUT", headers={"Content-Type": mime})
    urllib.request.urlopen(req, timeout=60)

    # Step 3: Confirm
    confirm_url = f"{API}/v1/files/confirm-upload?s3_key={urllib.parse.quote(s3_key)}&entity_type=document&entity_id={entity_id}"
    req = urllib.request.Request(confirm_url, data=b"", headers=hdrs, method="POST")
    urllib.request.urlopen(req, timeout=15)

    # Step 4: Create document record
    doc_payload = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "type_document": doc_type,
        "fichier_s3_key": s3_key,
        "fichier_nom_original": file_name,
        "fichier_taille_octets": file_size,
        "fichier_mime_type": mime,
    }
    for field in ["date_emission", "date_expiration", "numero_document", "organisme_emetteur"]:
        if field in metadata and metadata[field]:
            doc_payload[field] = metadata[field]

    req = urllib.request.Request(f"{API}/v1/documents", data=json.dumps(doc_payload).encode(), headers=hdrs)
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode())


def main():
    token = login()
    print("Logged in. Starting comprehensive data load...\n")

    stats = {"vehicle_updated": 0, "vehicle_created": 0, "docs_uploaded": 0, "drivers_updated": 0, "errors": 0}

    # ══════════════════════════════════════════════════════════════
    # 1. GET ALL VEHICLES (build immat→id map)
    # ══════════════════════════════════════════════════════════════
    print("=" * 60)
    print("STEP 1: Loading existing vehicles...")
    vehicles = api_get(token, "/v1/masterdata/vehicles?limit=50")
    items = vehicles.get("items", vehicles) if isinstance(vehicles, dict) else vehicles
    vehicle_map = {}  # immat → {id, ...}
    for v in items:
        immat = v.get("immatriculation") or v.get("plate_number", "")
        if immat:
            vehicle_map[immat] = v
    print(f"  Found {len(vehicle_map)} vehicles in system")

    # ══════════════════════════════════════════════════════════════
    # 2. UPDATE VEHICLES with registration cert data
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 2: Updating vehicles from registration certificates...")
    for reg in VEHICLE_REGISTRATION_DATA:
        immat = reg["immat"]
        existing = vehicle_map.get(immat)
        if not existing:
            print(f"  SKIP {immat} — not in system (will check insurance data)")
            continue

        vid = existing["id"]
        update = {"immatriculation": immat}

        # Only update fields that have values
        # NOTE: date_premiere_immatriculation causes 500 (server bug), use first_registration instead
        for key in ["marque", "modele", "ptac_kg", "carrosserie", "nb_essieux",
                     "norme_euro", "siren_proprietaire",
                     "proprietaire", "loueur_nom", "nombre_places"]:
            val = reg.get(key)
            if val is not None:
                update[key] = val

        # VIN: validate before sending (17 alphanumeric, no I/O/Q)
        vin = reg.get("vin")
        if vin and len(vin) == 17:
            import re
            if re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin.upper()):
                update["vin"] = vin.upper()
            else:
                print(f"  WARN {immat:12s} VIN {vin} has invalid chars, skipping VIN")
        elif vin:
            print(f"  WARN {immat:12s} VIN {vin} length={len(vin)}, skipping VIN")

        # NOTE: date_premiere_immatriculation and first_registration both cause 500 on PUT
        # This is a server bug — skipping date field for now. Data is in the registration cert PDFs.

        # Merge insurance data if available
        ins = INSURANCE_DATA.get(immat, {})
        for key in ["assurance_compagnie", "assurance_numero_police", "date_entree_flotte"]:
            if key in ins:
                update[key] = ins[key]

        try:
            api_put(token, f"/v1/masterdata/vehicles/{vid}", update)
            vin_str = update.get('vin', 'n/a')
            print(f"  OK   {immat:12s} vin={vin_str:17s} ptac={reg.get('ptac_kg',''):>5}")
            stats["vehicle_updated"] += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode() if hasattr(e, 'read') else str(e)
            print(f"  FAIL {immat:12s} — {e.code}: {body[:200]}")
            stats["errors"] += 1
        except Exception as e:
            print(f"  FAIL {immat:12s} — {e}")
            stats["errors"] += 1

    # ══════════════════════════════════════════════════════════════
    # 3. UPDATE remaining vehicles with insurance-only data
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 3: Updating vehicles with insurance data...")
    for immat, ins in INSURANCE_DATA.items():
        # Skip vehicles already updated in step 2
        already_in_reg = any(r["immat"] == immat for r in VEHICLE_REGISTRATION_DATA)

        existing = vehicle_map.get(immat)
        if not existing:
            # Create new vehicle (DA-483-GL)
            print(f"  CREATE {immat} — {ins['marque']} {ins['modele']}")
            try:
                create_payload = {
                    "immatriculation": immat,
                    "marque": ins["marque"],
                    "modele": ins["modele"],
                    "assurance_compagnie": ins["assurance_compagnie"],
                    "assurance_numero_police": ins["assurance_numero_police"],
                    "date_entree_flotte": ins["date_entree_flotte"],
                    "categorie": "PL_3_5T_19T",
                }
                result = api_post(token, "/v1/masterdata/vehicles", create_payload)
                vehicle_map[immat] = result
                print(f"  OK   {immat} created")
                stats["vehicle_created"] += 1
            except Exception as e:
                print(f"  FAIL create {immat} — {e}")
                stats["errors"] += 1
            continue

        if already_in_reg:
            continue  # Already handled

        vid = existing["id"]
        update = {"immatriculation": immat}
        for key in ["assurance_compagnie", "assurance_numero_police", "date_entree_flotte"]:
            if key in ins:
                update[key] = ins[key]

        try:
            api_put(token, f"/v1/masterdata/vehicles/{vid}", update)
            print(f"  OK   {immat:12s} insurance={ins['assurance_compagnie']}")
            stats["vehicle_updated"] += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode() if hasattr(e, 'read') else str(e)
            print(f"  FAIL {immat:12s} — {e.code}: {body[:200]}")
            stats["errors"] += 1
        except Exception as e:
            print(f"  FAIL {immat:12s} — {e}")
            stats["errors"] += 1

    # Refresh vehicle map
    vehicles = api_get(token, "/v1/masterdata/vehicles?limit=50")
    items = vehicles.get("items", vehicles) if isinstance(vehicles, dict) else vehicles
    vehicle_map = {}
    for v in items:
        immat = v.get("immatriculation") or v.get("plate_number", "")
        if immat:
            vehicle_map[immat] = v

    # ══════════════════════════════════════════════════════════════
    # 4. UPLOAD KBIS as company document
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 4: Uploading KBIS document...")
    kbis_path = os.path.join(BASE, "Extrait KBIS - SAF LOGISTIQUE -janvier 2026.pdf")
    if os.path.exists(kbis_path):
        try:
            result = upload_file_and_create_doc(
                token, "COMPANY", SAF_TENANT, "kbis",
                kbis_path,
                {"date_emission": "2026-01-21", "numero_document": "820904084",
                 "organisme_emetteur": "Greffe du Tribunal de Commerce de Pontoise"})
            print(f"  OK   KBIS uploaded (doc id: {result.get('id', '?')})")
            stats["docs_uploaded"] += 1
        except Exception as e:
            print(f"  FAIL KBIS — {e}")
            stats["errors"] += 1
    else:
        print(f"  SKIP KBIS — file not found")

    # ══════════════════════════════════════════════════════════════
    # 5. UPLOAD insurance memos per vehicle
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 5: Uploading insurance memos per vehicle...")
    memo_pdf = os.path.join(BASE, "Mémo Véhicule - Flotte n°11394791804.pdf")
    if os.path.exists(memo_pdf):
        for start_page, immat in MEMO_PAGE_MAP:
            veh = vehicle_map.get(immat)
            if not veh:
                print(f"  SKIP {immat} — not in system")
                continue

            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = tmp.name

                # Extract memo page (just the first page of the pair, not the contacts page)
                if not split_pdf_page(memo_pdf, start_page, tmp_path):
                    print(f"  FAIL {immat} — page {start_page} extraction failed")
                    stats["errors"] += 1
                    continue

                result = upload_file_and_create_doc(
                    token, "VEHICLE", veh["id"], "assurance",
                    tmp_path,
                    {"date_emission": "2026-02-26",
                     "numero_document": "0000011394791804",
                     "organisme_emetteur": "AXA France IARD"})
                print(f"  OK   {immat:12s} memo assurance uploaded")
                stats["docs_uploaded"] += 1
                os.unlink(tmp_path)
            except Exception as e:
                print(f"  FAIL {immat:12s} memo — {e}")
                stats["errors"] += 1
    else:
        print(f"  SKIP — memo PDF not found")

    # ══════════════════════════════════════════════════════════════
    # 6. UPLOAD registration certificates per vehicle
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 6: Uploading registration certificates per vehicle...")
    cert_pdf = os.path.join(BASE, "certificat d'immatriculation20260309_15380108.pdf")
    if os.path.exists(cert_pdf):
        for page_num, immat in CERT_PAGE_MAP:
            veh = vehicle_map.get(immat)
            if not veh:
                print(f"  SKIP {immat} — not in system")
                continue

            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = tmp.name

                if not split_pdf_page(cert_pdf, page_num, tmp_path):
                    print(f"  FAIL {immat} — page {page_num} extraction failed")
                    stats["errors"] += 1
                    continue

                # Find VIN from registration data
                reg = next((r for r in VEHICLE_REGISTRATION_DATA if r["immat"] == immat), {})
                result = upload_file_and_create_doc(
                    token, "VEHICLE", veh["id"], "carte_grise",
                    tmp_path,
                    {"numero_document": reg.get("vin", ""),
                     "organisme_emetteur": "Prefecture"})
                print(f"  OK   {immat:12s} carte grise uploaded")
                stats["docs_uploaded"] += 1
                os.unlink(tmp_path)
            except Exception as e:
                print(f"  FAIL {immat:12s} cert — {e}")
                stats["errors"] += 1
    else:
        print(f"  SKIP — cert PDF not found")

    # ══════════════════════════════════════════════════════════════
    # 7. UPDATE DRIVER QUALIFICATION FLAGS
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("STEP 7: Updating driver qualification flags...")
    drivers = api_get(token, "/v1/masterdata/drivers?limit=50")
    driver_items = drivers.get("items", drivers) if isinstance(drivers, dict) else drivers
    driver_map = {}
    for d in driver_items:
        nom = d.get("nom", "")
        prenom = d.get("prenom", "")
        full = f"{nom} {prenom}"
        driver_map[full] = d

    for name, quals in DRIVER_QUALIFICATIONS.items():
        if not quals:
            continue
        # Try to find driver
        driver = driver_map.get(name)
        if not driver:
            # Try reverse lookup
            for full, d in driver_map.items():
                if name.upper() in full.upper():
                    driver = d
                    break
        if not driver:
            print(f"  SKIP {name} — not found")
            continue

        did = driver["id"]
        update = {
            "nom": driver["nom"],
            "prenom": driver["prenom"],
        }
        changed = False
        if quals.get("fimo") and not driver.get("qualification_fimo"):
            update["qualification_fimo"] = True
            changed = True
        if quals.get("adr") and not driver.get("qualification_adr"):
            update["qualification_adr"] = True
            changed = True

        if not changed:
            continue

        try:
            api_put(token, f"/v1/masterdata/drivers/{did}", update)
            flags = []
            if update.get("qualification_fimo"):
                flags.append("FIMO")
            if update.get("qualification_adr"):
                flags.append("ADR")
            print(f"  OK   {name:25s} flags={','.join(flags)}")
            stats["drivers_updated"] += 1
        except Exception as e:
            print(f"  FAIL {name:25s} — {e}")
            stats["errors"] += 1

    # ══════════════════════════════════════════════════════════════
    # SUMMARY
    # ══════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("LOAD COMPLETE")
    print(f"  Vehicles updated:  {stats['vehicle_updated']}")
    print(f"  Vehicles created:  {stats['vehicle_created']}")
    print(f"  Documents uploaded: {stats['docs_uploaded']}")
    print(f"  Drivers updated:   {stats['drivers_updated']}")
    print(f"  Errors:            {stats['errors']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
