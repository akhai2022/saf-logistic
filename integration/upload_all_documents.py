#!/usr/bin/env python3
"""
Upload all integration documents to SAF Logistic production.
Splits multi-page PDFs and uploads each page as the correct document type.
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

# ── Driver ID mapping (from system) ──
DRIVERS = {
    "ABDALLAH Fouad": "0c19cd4b-9993-4dd3-ada5-37a5b48c3e2c",
    "ABDALLAH Khaled": "2f148425-f279-4845-89a6-4e06eb8f8081",
    "ABDALLAH Sofiane": "34a75a24-3f66-4db6-91ab-e0815b5abc3c",
    "BENACHOUR Kamel": "bd8cb722-daca-498c-a2de-956a9ebd13fd",
    "BENALI Mokhtar": "3dfc29b3-0b46-4b7a-b372-d6f24e6248ab",
    "BENALLOU Mohammed": "9102a3da-bc3c-4cca-bf5a-0c97dec0b40f",
    "BETTIOUI Badr": "2d516f01-d8b6-45ea-8fe1-c3e46452f3d3",
    "BOUKZINE Mouloud": "7353aeec-5290-4fff-a1c8-0639858a92e4",
    "BRILLANT Eddy": "3e33eb3a-5e30-4252-8ec9-21583c7e5ecf",
    "DOUZI Mohammed": "a9b4aa72-e23e-4e70-975d-8f29797591d7",
    "DRAME Abdou": "09b142fc-b38b-44de-a362-33dbcdedd97c",
    "EL IDRISSI Rachid": "f9c48033-8687-44e0-a5e0-936fbfd66d94",
    "GHANDOUR Abdallah": "2fedee37-3238-4120-9a78-bb3658924275",
    "GOMIS Yohan": "f9b5b286-d939-4409-9c90-d87c2cce6bb8",
    "KARRADA Youssef": "33c4d85f-d800-49ba-b121-7f7db13612cd",
    "KONATE Youssouf": "7b0630db-533c-4161-80b1-68f89efb551f",
    "MADJID Abderrahmane": "a7754785-6066-4666-b1ff-cb26e9050148",
    "MAJD Rachid": "cc8ae22f-8370-453b-9673-e9932257cf74",
    "OULAIN Mustapha": "608db5e4-ea1d-433d-b157-921cb2b5613a",
    "WAMBA Christian": "5a865a91-c9c5-42c1-9d42-b49834ed827f",
}

# ── Vehicle ID mapping ──
VEHICLES = {
    "CH-398-HL": "d337d519-c33c-40e1-b05e-580b803eca5a",
    "AW-639-SE": "f4ac2007-1a01-4598-88e8-f35512ba3909",
    "BZ-627-AM": "cc8c35a0-69c7-4fcf-8609-6b987e4bbab0",
    "AK-768-JX": "c2ae26de-c32b-486f-b14f-6aba836e4712",
    "CT-529-GA": "3b1e6649-828a-43aa-875a-affeac4cef80",
    "DX-485-WV": "7d196ef6-65f5-4972-b12d-67b22d2b33ef",
}

# ── Document definitions ──
# Format: (pdf_path, pages_to_extract, driver_or_vehicle_name, entity_type, documents_per_page)
# documents_per_page: list of (page_num, doc_type, metadata_dict)

DRIVER_DOCS = [
    # ABDALLAH Fouad — from conducteur/FOUAD*.pdf
    ("conducteur/FOUAD20260310_14343979.pdf", "ABDALLAH Fouad", [
        (1, "fimo", {"numero_document": "040192301117", "date_emission": "2022-11-26", "date_expiration": "2027-11-25", "organisme_emetteur": "Imprimerie Nationale"}),
        (3, "permis_conduire", {"numero_document": "23AW67402", "date_emission": "2023-11-02", "date_expiration": "2028-11-02", "organisme_emetteur": "Préfet 92"}),
    ]),
    ("ABDALLAH Fouad recto.pdf", "ABDALLAH Fouad", [
        (1, "carte_conducteur", {"numero_document": "040192301573", "date_emission": "2023-12-19", "date_expiration": "2028-12-18", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),
    ("ABDALLAH Fouad verso.pdf", "ABDALLAH Fouad", [
        (1, "adr", {"numero_document": "FR000001229010", "date_expiration": "2026-11-05", "organisme_emetteur": "PROMOTRANS"}),
    ]),

    # ABDALLAH Sofiane
    ("ABDALLAH Sofiane.pdf", "ABDALLAH Sofiane", [
        (1, "carte_identite", {"numero_document": "HGRP4LCC3", "date_emission": "2021-06-07", "date_expiration": "2031-06-06"}),
        (3, "fimo", {"numero_document": "030995100379", "date_emission": "2022-06-25", "date_expiration": "2027-06-24", "organisme_emetteur": "Imprimerie Nationale"}),
        (4, "carte_conducteur", {"numero_document": "030995100379", "date_emission": "2018-04-13", "date_expiration": "2023-04-13", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # BENACHOUR Kamel
    ("BENACHOUR Kamel.pdf", "BENACHOUR Kamel", [
        (1, "permis_conduire", {"numero_document": "20AV11795", "date_emission": "2020-12-07", "date_expiration": "2025-12-07", "organisme_emetteur": "Préfet 92"}),
        (1, "fimo", {"numero_document": "140992300535", "date_emission": "2021-02-06", "date_expiration": "2026-02-05", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "adr", {"numero_document": "FR00000399916000", "date_expiration": "2028-10-17", "organisme_emetteur": "AFTRAL"}),
        (3, "carte_identite", {"numero_document": "68C2BDB69", "date_expiration": "2035-05-26"}),
    ]),

    # BENALI Mokhtar
    ("BENALI Mokthar.pdf", "BENALI Mokhtar", [
        (1, "carte_identite", {"numero_document": "9V3N8LCVW", "date_expiration": "2025-01-18"}),
        (2, "permis_conduire", {"numero_document": "23AI37271", "date_emission": "2023-04-19", "date_expiration": "2028-04-19", "organisme_emetteur": "Préfet 92"}),
        (2, "carte_conducteur", {"numero_document": "230492301573", "date_emission": "2023-06-01", "date_expiration": "2028-05-31", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # BENALLOU Mohammed
    ("conducteur/BENALOU Mohamed.pdf", "BENALLOU Mohammed", [
        (1, "fimo", {"numero_document": "080278100240", "date_emission": "2023-05-27", "date_expiration": "2028-05-26", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "carte_conducteur", {"numero_document": "080278100240", "date_emission": "2023-06-05", "date_expiration": "2028-06-04", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "permis_conduire", {"numero_document": "23AW45002", "date_emission": "2023-10-30", "date_expiration": "2028-10-30", "organisme_emetteur": "Préfet 78"}),
    ]),

    # BETTIOUI Badr
    ("BETTIOUI Badr.pdf", "BETTIOUI Badr", [
        (1, "fimo", {"numero_document": "220382200332", "date_emission": "2022-06-08", "date_expiration": "2027-06-08", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "permis_conduire", {"numero_document": "22AG59297", "date_emission": "2021-03-19", "date_expiration": "2026-03-19", "organisme_emetteur": "Préfet 82"}),
        (1, "carte_conducteur", {"numero_document": "220382200332", "date_emission": "2022-06-10", "date_expiration": "2027-06-09", "organisme_emetteur": "Imprimerie Nationale"}),
        (2, "adr", {"numero_document": "FR000000040054600", "date_expiration": "2028-11-28", "organisme_emetteur": "PROMOTRANS"}),
    ]),

    # BOUKZINE Mouloud
    ("conducteur/BOUKZINE MOULOUD20260305_13264517.pdf", "BOUKZINE Mouloud", [
        (1, "fimo", {"numero_document": "010478100085", "date_emission": "2023-01-07", "date_expiration": "2028-01-08", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "permis_conduire", {"numero_document": "21AX12336", "date_emission": "2021-06-08", "date_expiration": "2026-12-08", "organisme_emetteur": "Préfet 78"}),
        (3, "carte_conducteur", {"numero_document": "010478100085", "date_emission": "2024-10-01", "date_expiration": "2029-09-30", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # BRILLANT Eddy
    ("BRILLANT Eddy.pdf", "BRILLANT Eddy", [
        (1, "adr", {"numero_document": "FR00000368147000", "date_expiration": "2028-01-05", "organisme_emetteur": "PROMOTRANS"}),
        (1, "carte_identite", {"numero_document": "V6RB64EY4", "date_emission": "2021-12-14", "date_expiration": "2031-12-13"}),
        (1, "permis_conduire", {"numero_document": "23AK39170", "date_emission": "2023-05-22", "date_expiration": "2028-05-22", "organisme_emetteur": "Préfet 93"}),
        (1, "fimo", {"numero_document": "070193200363", "date_emission": "2023-04-08", "date_expiration": "2028-04-07", "organisme_emetteur": "Imprimerie Nationale"}),
        (3, "carte_conducteur", {"numero_document": "070193200363", "date_emission": "2023-06-21", "date_expiration": "2028-06-20", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # DOUZI Mohammed
    ("DOUZI Mohamed.pdf", "DOUZI Mohammed", [
        (1, "carte_conducteur", {"numero_document": "U18M48886L", "date_emission": "2023-12-11", "date_expiration": "2028-12-10", "organisme_emetteur": "Imprimerie Nationale"}),
        (2, "fimo", {"numero_document": "U169X4769K", "date_emission": "2024-12-07", "date_expiration": "2029-12-06", "organisme_emetteur": "Imprimerie Nationale"}),
        (3, "adr", {"numero_document": "FR00000296127000", "date_expiration": "2026-01-05", "organisme_emetteur": "AFTRAL"}),
        (4, "carte_identite", {"numero_document": "81SXAK3AE", "date_expiration": "2026-05-09"}),
    ]),

    # DRAME Abdou
    ("DRAME Abdou.pdf", "DRAME Abdou", [
        (1, "carte_identite", {"numero_document": "6S9H1LOH5", "date_expiration": "2026-11-28"}),
        (1, "permis_conduire", {"numero_document": "24AT33392", "date_emission": "2024-08-01", "date_expiration": "2029-08-01", "organisme_emetteur": "Préfet 95"}),
        (1, "carte_conducteur", {"numero_document": "180660100711", "date_emission": "2024-10-07", "date_expiration": "2029-10-06", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "fimo", {"numero_document": "180660100711", "date_emission": "2025-05-31", "date_expiration": "2030-05-30", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # EL IDRISSI Rachid
    ("conducteur/IDRISSI RACHID20260305_12241081.pdf", "EL IDRISSI Rachid", [
        (1, "permis_conduire", {"numero_document": "25AW75344", "date_emission": "2025-09-18", "date_expiration": "2030-09-18", "organisme_emetteur": "Préfet 78"}),
        (1, "fimo", {"numero_document": "000216200047", "date_emission": "2024-02-10", "date_expiration": "2029-02-09", "organisme_emetteur": "Imprimerie Nationale"}),
        (2, "adr", {"numero_document": "FR000000360020", "date_expiration": "2030-08-23", "organisme_emetteur": "AFTRAL"}),
    ]),

    # GHANDOUR Abdallah
    ("GHANDOUR Abdallah .pdf", "GHANDOUR Abdallah", [
        (1, "permis_conduire", {"numero_document": "23BB29836", "date_emission": "2023-12-20", "date_expiration": "2028-12-20", "organisme_emetteur": "Préfet 92"}),
        (2, "adr", {"numero_document": "FR00000236690010", "date_emission": "2024-02-27", "date_expiration": "2029-02-27", "organisme_emetteur": "AFTRAL"}),
    ]),

    # GOMIS Yohan
    ("conducteur/GOMIS20260310_14232342.pdf", "GOMIS Yohan", [
        (1, "permis_conduire", {"numero_document": "25BB44213", "date_emission": "2025-11-06", "date_expiration": "2030-11-06", "organisme_emetteur": "Préfet 78"}),
        (3, "fimo", {"numero_document": "150578100100", "date_emission": "2025-12-30", "date_expiration": "2030-12-29", "organisme_emetteur": "Imprimerie Nationale"}),
        (5, "carte_conducteur", {"numero_document": "150578100100", "date_emission": "2025-12-16", "date_expiration": "2030-12-15", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # KARRADA Youssef
    ("KARRADA Youssef.pdf", "KARRADA Youssef", [
        (1, "permis_conduire", {"numero_document": "21AJ47195", "date_emission": "2021-05-28", "date_expiration": "2026-05-28", "organisme_emetteur": "Préfet 95"}),
        (1, "fimo", {"numero_document": "000659501799", "date_emission": "2021-12-21", "date_expiration": "2027-02-03", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "carte_conducteur", {"numero_document": "000659501799", "date_emission": "2022-04-19", "date_expiration": "2027-04-18", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # KONATE Youssouf
    ("KONATE Youssouf.pdf", "KONATE Youssouf", [
        (1, "carte_identite", {"numero_document": "200295352124", "date_expiration": "2035-02-09"}),
        (1, "adr", {"numero_document": "FR000024833940", "date_expiration": "2029-04-09", "organisme_emetteur": "AFTRAL"}),
        (1, "carte_conducteur", {"numero_document": "150893100988", "date_emission": "2024-08-12", "date_expiration": "2029-08-11", "organisme_emetteur": "Imprimerie Nationale"}),
        (2, "permis_conduire", {"numero_document": "24AU34337", "date_emission": "2024-08-14", "date_expiration": "2029-08-14", "organisme_emetteur": "Préfet 95"}),
        (2, "fimo", {"numero_document": "150893100988", "date_emission": "2024-07-08", "date_expiration": "2029-07-05", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # MADJID Abderrahmane
    ("MADJID Abderrahmane.pdf", "MADJID Abderrahmane", [
        (1, "carte_conducteur", {"numero_document": "041292300863", "date_emission": "2023-04-25", "date_expiration": "2028-04-24", "organisme_emetteur": "Imprimerie Nationale"}),
        (2, "fimo", {"numero_document": "041292300869", "date_emission": "2023-11-11", "date_expiration": "2028-11-10", "organisme_emetteur": "Imprimerie Nationale"}),
        (2, "carte_identite", {"numero_document": "ZHV6BSRVS", "date_expiration": "2035-05-09"}),
        (3, "permis_conduire", {"numero_document": "25AL38936", "date_emission": "2025-05-09", "date_expiration": "2030-05-09", "organisme_emetteur": "Préfet 95"}),
        (3, "adr", {"numero_document": "FR00000311435000", "date_expiration": "2026-04-09", "organisme_emetteur": "PROMOTRANS"}),
    ]),

    # MAJD Rachid
    ("MAJD Rachid .pdf", "MAJD Rachid", [
        (1, "carte_identite", {"numero_document": "180295352053", "date_expiration": "2033-02-07"}),
        (3, "carte_conducteur", {"numero_document": "016923005​67", "date_emission": "2025-02-25", "date_expiration": "2030-02-24", "organisme_emetteur": "Imprimerie Nationale"}),
        (4, "fimo", {"numero_document": "016923003​67", "date_emission": "2025-09-13", "date_expiration": "2030-09-12", "organisme_emetteur": "Imprimerie Nationale"}),
        (5, "permis_conduire", {"numero_document": "23AF08709", "date_emission": "2023-03-08", "date_expiration": "2028-03-08", "organisme_emetteur": "Préfet 95"}),
    ]),

    # OULAIN Mustapha
    ("OULAIN Mustapha.pdf", "OULAIN Mustapha", [
        (1, "carte_identite", {"numero_document": "JOTWLSDQV", "date_expiration": "2034-04-09"}),
        (3, "fimo", {"numero_document": "241278401913", "date_emission": "2025-04-29", "date_expiration": "2030-04-28", "organisme_emetteur": "Imprimerie Nationale"}),
        (3, "permis_conduire", {"numero_document": "25AC41094", "date_emission": "2025-01-28", "date_expiration": "2030-01-28", "organisme_emetteur": "Préfet 78"}),
        (3, "carte_conducteur", {"numero_document": "241278401913", "date_emission": "2025-04-30", "date_expiration": "2030-04-29", "organisme_emetteur": "Imprimerie Nationale"}),
    ]),

    # WAMBA Christian
    ("WAMBA Christian.pdf", "WAMBA Christian", [
        (1, "permis_conduire", {"numero_document": "22AZ11019", "date_emission": "2022-12-06", "date_expiration": "2027-12-06", "organisme_emetteur": "Préfet 95"}),
        (1, "fimo", {"numero_document": "141295300398", "date_emission": "2022-06-08", "date_expiration": "2027-06-07", "organisme_emetteur": "Imprimerie Nationale"}),
        (1, "carte_conducteur", {"numero_document": "141295300398", "date_emission": "2022-12-27", "date_expiration": "2027-12-26", "organisme_emetteur": "Imprimerie Nationale"}),
        (2, "adr", {"numero_document": "FR00002484464000", "date_expiration": "2029-05-22", "organisme_emetteur": "AFTRAL"}),
        (3, "carte_identite", {"numero_document": "160795100432", "date_emission": "2016-07-22", "date_expiration": "2031-07-21"}),
    ]),

    # DAHDOUD Abdelhadi — not in system, skip or create
    # ("conducteur/DAHDOUD20260305_13301951.pdf", "DAHDOUD Abdelhadi", [...]),
]

# Vehicle control documents
VEHICLE_DOCS = [
    ("Contrôle technique des véhicules20260325_12522858.pdf", [
        (1, "CH-398-HL", "controle_technique", {"date_emission": "2025-12-08", "date_expiration": "2026-12-29", "numero_document": "25899966", "organisme_emetteur": "SOCEO 92"}),
        (2, "AW-639-SE", "controle_technique", {"date_emission": "2025-07-11", "date_expiration": "2026-07-18", "numero_document": "25895534", "organisme_emetteur": "SOCEO 92"}),
        (3, "BZ-627-AM", "controle_technique", {"date_emission": "2026-08-16", "date_expiration": "2027-01-15", "numero_document": "26802368", "organisme_emetteur": "SOCEO 92"}),
        (4, "AK-768-JX", "controle_technique", {"date_emission": "2026-02-06", "date_expiration": "2027-02-08", "numero_document": "26061147", "organisme_emetteur": "SOCEO 92"}),
        (5, "CT-529-GA", "controle_technique", {"date_emission": "2026-01-17", "date_expiration": "2027-01-16", "numero_document": "26199579", "organisme_emetteur": "SARL ROISSY TEST PL"}),
        (6, "DX-485-WV", "controle_technique", {"date_emission": "2025-10-03", "date_expiration": "2026-10-02", "numero_document": "25195415", "organisme_emetteur": "SARL ROISSY TEST PL"}),
    ]),
]


def login():
    data = json.dumps({"email": "admin@saf-logistique.fr", "password": "SafAdmin2026!", "tenant_id": SAF_TENANT}).encode()
    req = urllib.request.Request(f"{API}/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode())["access_token"]


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


def upload_document(token, entity_type, entity_id, doc_type, file_path, metadata):
    """Upload a document file and create the document record."""
    hdrs = {"Authorization": f"Bearer {token}", "X-Tenant-ID": SAF_TENANT, "Content-Type": "application/json"}

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    mime = "application/pdf" if file_path.endswith(".pdf") else "image/jpeg"

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
    print(f"Logged in. Processing documents...\n")

    total = 0
    errors = 0

    # ── Driver documents ──
    for pdf_rel, driver_name, docs in DRIVER_DOCS:
        driver_id = DRIVERS.get(driver_name)
        if not driver_id:
            print(f"  SKIP {driver_name} — not in system")
            continue

        pdf_path = os.path.join(BASE, pdf_rel)
        if not os.path.exists(pdf_path):
            print(f"  SKIP {pdf_rel} — file not found")
            continue

        # Group docs by page
        pages_needed = set(d[0] for d in docs)

        for page_num, doc_type, metadata in docs:
            total += 1
            try:
                # For multi-page PDFs, extract the specific page
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = tmp.name

                if pdf_path.endswith(".jpg"):
                    tmp_path = pdf_path  # Use directly for JPGs
                else:
                    if not split_pdf_page(pdf_path, page_num, tmp_path):
                        print(f"  FAIL {driver_name} {doc_type} — page {page_num} extraction failed")
                        errors += 1
                        continue

                result = upload_document(token, "DRIVER", driver_id, doc_type, tmp_path, metadata)
                exp = metadata.get("date_expiration", "—")
                print(f"  OK   {driver_name:25s} {doc_type:20s} exp={exp}")

                if tmp_path != pdf_path:
                    os.unlink(tmp_path)

            except Exception as e:
                print(f"  FAIL {driver_name:25s} {doc_type:20s} — {e}")
                errors += 1

    # ── Vehicle documents ──
    for pdf_rel, vehicle_docs in VEHICLE_DOCS:
        pdf_path = os.path.join(BASE, pdf_rel)
        if not os.path.exists(pdf_path):
            print(f"  SKIP {pdf_rel} — file not found")
            continue

        for page_num, immat, doc_type, metadata in vehicle_docs:
            vehicle_id = VEHICLES.get(immat)
            if not vehicle_id:
                print(f"  SKIP vehicle {immat} — not in system")
                continue

            total += 1
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = tmp.name

                if not split_pdf_page(pdf_path, page_num, tmp_path):
                    print(f"  FAIL vehicle {immat} {doc_type} — page extraction failed")
                    errors += 1
                    continue

                result = upload_document(token, "VEHICLE", vehicle_id, doc_type, tmp_path, metadata)
                exp = metadata.get("date_expiration", "—")
                print(f"  OK   vehicle {immat:12s} {doc_type:20s} exp={exp}")
                os.unlink(tmp_path)

            except Exception as e:
                print(f"  FAIL vehicle {immat:12s} {doc_type:20s} — {e}")
                errors += 1

    print(f"\n{'='*60}")
    print(f"Done: {total - errors}/{total} uploaded, {errors} errors")


if __name__ == "__main__":
    main()
