#!/usr/bin/env python3
"""
Check for duplicates across ALL entities in SAF Logistic production API.
READ-ONLY: no modifications are made.
"""

import json
import urllib.request
import urllib.error
import ssl
from collections import defaultdict

BASE_URL = "https://api-saf.dataforgeai.fr"
EMAIL = "admin@saf-logistique.fr"
PASSWORD = "SafAdmin2026!"
TENANT_ID = "10000000-0000-0000-0000-000000000001"

# Allow redirects and handle SSL
ssl_ctx = ssl.create_default_context()


def login():
    """Authenticate and return access token."""
    url = f"{BASE_URL}/v1/auth/login"
    payload = json.dumps({
        "email": EMAIL,
        "password": PASSWORD,
        "tenant_id": TENANT_ID,
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, context=ssl_ctx) as resp:
        data = json.loads(resp.read().decode())
    token = data.get("access_token") or data.get("token")
    if not token:
        # Try nested structures
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, str) and len(v) > 20:
                    token = v
                    break
                if isinstance(v, dict):
                    token = v.get("access_token") or v.get("token")
                    if token:
                        break
    if not token:
        print("Login response (keys):", list(data.keys()) if isinstance(data, dict) else type(data))
        print("Login response:", json.dumps(data, indent=2, default=str)[:500])
        raise RuntimeError("Could not extract token from login response")
    return token


def api_get(path, token):
    """GET request with auth, following redirects."""
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(
        url, method="GET",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Tenant-ID": TENANT_ID,
        },
    )
    try:
        with urllib.request.urlopen(req, context=ssl_ctx) as resp:
            raw = resp.read().decode()
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"  HTTP {e.code} on GET {path}: {body[:300]}")
        return None


def extract_items(data):
    """Extract list of items from various response shapes."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Common patterns: {items: [...]}, {data: [...]}, {results: [...]}
        for key in ("items", "data", "results", "documents", "vehicles", "drivers", "clients", "templates"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # If the dict has numeric-ish keys or a single list value
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def check_documents(token):
    """Check documents for duplicates by (entity_type, entity_id, type_document)."""
    print("\n" + "=" * 70)
    print("1. DOCUMENTS — duplicates by (entity_type, entity_id, type_document)")
    print("=" * 70)

    data = api_get("/v1/documents?limit=500", token)
    if data is None:
        print("  Could not fetch documents.")
        return

    items = extract_items(data)
    print(f"  Total documents fetched: {len(items)}")

    if not items:
        print("  No documents found.")
        return

    # Show sample keys for debugging
    if items:
        print(f"  Sample document keys: {list(items[0].keys())}")

    groups = defaultdict(list)
    for doc in items:
        entity_type = doc.get("entity_type", "?")
        entity_id = doc.get("entity_id", "?")
        type_doc = doc.get("type_document", doc.get("document_type", doc.get("type", "?")))
        key = (entity_type, str(entity_id), type_doc)
        groups[key].append(doc)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if not duplicates:
        print("  No duplicate documents found.")
    else:
        print(f"  Found {len(duplicates)} duplicate group(s):\n")
        for (etype, eid, ttype), docs in sorted(duplicates.items()):
            print(f"  [{len(docs)}x] entity_type={etype}, entity_id={eid}, type_document={ttype}")
            for d in docs:
                doc_id = d.get("id", "?")
                filename = d.get("filename", d.get("file_name", d.get("name", "?")))
                created = d.get("created_at", d.get("date_creation", "?"))
                print(f"       id={doc_id}  filename={filename}  created={created}")


def check_vehicles(token):
    """Check vehicles for duplicate immatriculation."""
    print("\n" + "=" * 70)
    print("2. VEHICLES — duplicates by immatriculation")
    print("=" * 70)

    data = api_get("/v1/masterdata/vehicles?limit=50", token)
    if data is None:
        print("  Could not fetch vehicles.")
        return

    items = extract_items(data)
    print(f"  Total vehicles fetched: {len(items)}")

    if not items:
        print("  No vehicles found.")
        return

    if items:
        print(f"  Sample vehicle keys: {list(items[0].keys())}")

    groups = defaultdict(list)
    for v in items:
        immat = (v.get("immatriculation") or v.get("registration") or v.get("plate") or "?").strip().upper()
        if immat and immat != "?":
            groups[immat].append(v)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if not duplicates:
        print("  No duplicate vehicles found.")
    else:
        print(f"  Found {len(duplicates)} duplicate group(s):\n")
        for immat, vehicles in sorted(duplicates.items()):
            print(f"  [{len(vehicles)}x] immatriculation={immat}")
            for v in vehicles:
                vid = v.get("id", "?")
                marque = v.get("marque", v.get("brand", "?"))
                modele = v.get("modele", v.get("model", "?"))
                print(f"       id={vid}  marque={marque}  modele={modele}")


def check_drivers(token):
    """Check drivers for duplicate nom+prenom."""
    print("\n" + "=" * 70)
    print("3. DRIVERS — duplicates by (nom, prenom)")
    print("=" * 70)

    data = api_get("/v1/masterdata/drivers?limit=50", token)
    if data is None:
        print("  Could not fetch drivers.")
        return

    items = extract_items(data)
    print(f"  Total drivers fetched: {len(items)}")

    if not items:
        print("  No drivers found.")
        return

    if items:
        print(f"  Sample driver keys: {list(items[0].keys())}")

    groups = defaultdict(list)
    for d in items:
        nom = (d.get("nom") or d.get("last_name") or "?").strip().upper()
        prenom = (d.get("prenom") or d.get("first_name") or "?").strip().upper()
        key = (nom, prenom)
        groups[key].append(d)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if not duplicates:
        print("  No duplicate drivers found.")
    else:
        print(f"  Found {len(duplicates)} duplicate group(s):\n")
        for (nom, prenom), drivers in sorted(duplicates.items()):
            print(f"  [{len(drivers)}x] nom={nom}, prenom={prenom}")
            for d in drivers:
                did = d.get("id", "?")
                tel = d.get("telephone", d.get("phone", "?"))
                print(f"       id={did}  telephone={tel}")


def check_clients(token):
    """Check clients for duplicate raison_sociale / name."""
    print("\n" + "=" * 70)
    print("4. CLIENTS — duplicates by raison_sociale / name")
    print("=" * 70)

    data = api_get("/v1/masterdata/clients?limit=50", token)
    if data is None:
        print("  Could not fetch clients.")
        return

    items = extract_items(data)
    print(f"  Total clients fetched: {len(items)}")

    if not items:
        print("  No clients found.")
        return

    if items:
        print(f"  Sample client keys: {list(items[0].keys())}")

    groups = defaultdict(list)
    for c in items:
        name = (
            c.get("raison_sociale")
            or c.get("name")
            or c.get("company_name")
            or c.get("nom")
            or "?"
        ).strip().upper()
        if name and name != "?":
            groups[name].append(c)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if not duplicates:
        print("  No duplicate clients found.")
    else:
        print(f"  Found {len(duplicates)} duplicate group(s):\n")
        for name, clients in sorted(duplicates.items()):
            print(f"  [{len(clients)}x] raison_sociale={name}")
            for c in clients:
                cid = c.get("id", "?")
                siret = c.get("siret", "?")
                print(f"       id={cid}  siret={siret}")


def check_compliance_templates(token):
    """Check compliance templates for duplicate (entity_type, type_document)."""
    print("\n" + "=" * 70)
    print("5. COMPLIANCE TEMPLATES — duplicates by (entity_type, type_document)")
    print("=" * 70)

    data = api_get("/v1/compliance/templates", token)
    if data is None:
        print("  Could not fetch compliance templates.")
        return

    items = extract_items(data)
    print(f"  Total templates fetched: {len(items)}")

    if not items:
        print("  No templates found.")
        return

    if items:
        print(f"  Sample template keys: {list(items[0].keys())}")

    groups = defaultdict(list)
    for t in items:
        entity_type = t.get("entity_type", "?")
        type_doc = t.get("type_document", t.get("document_type", t.get("type", "?")))
        key = (entity_type, type_doc)
        groups[key].append(t)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    if not duplicates:
        print("  No duplicate compliance templates found.")
    else:
        print(f"  Found {len(duplicates)} duplicate group(s):\n")
        for (etype, ttype), templates in sorted(duplicates.items()):
            print(f"  [{len(templates)}x] entity_type={etype}, type_document={ttype}")
            for t in templates:
                tid = t.get("id", "?")
                name = t.get("name", t.get("nom", "?"))
                active = t.get("is_active", t.get("active", "?"))
                print(f"       id={tid}  name={name}  active={active}")


def main():
    print("SAF Logistic Production API — Duplicate Check Report")
    print("=" * 70)
    print(f"API: {BASE_URL}")
    print("Mode: READ-ONLY\n")

    print("Logging in...")
    token = login()
    print("Authenticated successfully.\n")

    check_documents(token)
    check_vehicles(token)
    check_drivers(token)
    check_clients(token)
    check_compliance_templates(token)

    print("\n" + "=" * 70)
    print("DUPLICATE CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
