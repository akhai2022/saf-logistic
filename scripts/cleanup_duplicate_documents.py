#!/usr/bin/env python3
"""
Cleanup duplicate documents on SAF Logistic production API.

Groups documents by (entity_type, entity_id, type_document).
For each group with >1 document, keeps the LATEST (by created_at)
and rejects all others with motif "Doublon supprime lors du nettoyage".

Rejecting sets statut=REJETE which the compliance engine already ignores.
"""
import json
import ssl
import urllib.request
from collections import defaultdict
from datetime import datetime

API_BASE = "https://api-saf.dataforgeai.fr"
EMAIL = "admin@saf-logistique.fr"
PASSWORD = "SafAdmin2026!"
TENANT_ID = "10000000-0000-0000-0000-000000000001"

REJECT_MOTIF = "Doublon supprime lors du nettoyage"


def make_opener():
    """Create an opener that follows redirects for all HTTP methods (including PATCH)."""
    # Custom redirect handler that preserves method and body on redirects
    class MethodPreservingRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            # Build a new request preserving the original method and body
            new_req = urllib.request.Request(
                newurl,
                data=req.data,
                headers=dict(req.headers),
                method=req.get_method(),
            )
            return new_req

    ctx = ssl.create_default_context()
    https_handler = urllib.request.HTTPSHandler(context=ctx)
    opener = urllib.request.build_opener(https_handler, MethodPreservingRedirectHandler)
    return opener


def api_request(opener, method, path, token=None, body=None):
    """Make an API request and return parsed JSON."""
    url = f"{API_BASE}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Tenant-ID", TENANT_ID)
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    resp = opener.open(req)
    raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else None


def login(opener):
    """Authenticate and return access token."""
    payload = {
        "email": EMAIL,
        "password": PASSWORD,
        "tenant_id": TENANT_ID,
    }
    data = api_request(opener, "POST", "/v1/auth/login", body=payload)
    token = data["access_token"]
    print(f"Logged in as {EMAIL} (role: {data.get('role', '?')})")
    return token


def fetch_all_documents(opener, token):
    """Fetch all documents with limit=500."""
    docs = api_request(opener, "GET", "/v1/documents?limit=500", token=token)
    print(f"Fetched {len(docs)} documents total")
    return docs


def reject_document(opener, token, doc_id):
    """Reject a document by ID."""
    body = {
        "statut": "REJETE",
        "motif_rejet": REJECT_MOTIF,
    }
    result = api_request(opener, "PATCH", f"/v1/documents/{doc_id}/reject", token=token, body=body)
    return result


def parse_created_at(doc):
    """Parse created_at field for sorting. Returns a datetime or epoch for None."""
    val = doc.get("created_at")
    if not val:
        return datetime.min
    # Try multiple formats
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(val[:26], fmt)
        except ValueError:
            continue
    # Fallback: just use string comparison
    return datetime.min


def main():
    opener = make_opener()

    # Step 1: Login
    token = login(opener)

    # Step 2: Fetch all documents
    docs = fetch_all_documents(opener, token)

    # Step 3: Group by (entity_type, entity_id, type_document)
    groups = defaultdict(list)
    skipped_statuses = defaultdict(int)

    for doc in docs:
        entity_type = doc.get("entity_type", "")
        entity_id = doc.get("entity_id", "")
        type_doc = doc.get("type_document") or doc.get("doc_type") or ""
        statut = doc.get("statut", "")

        # Skip already rejected/archived documents - they're not duplicates to clean
        if statut in ("REJETE", "ARCHIVE"):
            skipped_statuses[statut] += 1
            continue

        key = (entity_type, entity_id, type_doc)
        groups[key].append(doc)

    print(f"\nSkipped {sum(skipped_statuses.values())} docs with status: {dict(skipped_statuses)}")
    print(f"Grouped remaining docs into {len(groups)} unique (entity_type, entity_id, type_document) groups")

    # Step 4: Find duplicates
    total_rejected = 0
    groups_with_dupes = 0

    for key, group_docs in sorted(groups.items()):
        if len(group_docs) <= 1:
            continue

        groups_with_dupes += 1
        entity_type, entity_id, type_doc = key

        # Sort by created_at descending - keep the latest
        group_docs.sort(key=parse_created_at, reverse=True)
        keeper = group_docs[0]
        to_reject = group_docs[1:]

        print(f"\n--- Group: entity_type={entity_type}, entity_id={entity_id}, type_document={type_doc} ---")
        print(f"  {len(group_docs)} documents found. Keeping latest: id={keeper['id']} (created_at={keeper.get('created_at')}, statut={keeper.get('statut')})")

        for doc in to_reject:
            doc_id = doc["id"]
            print(f"  Rejecting: id={doc_id} (created_at={doc.get('created_at')}, statut={doc.get('statut')})")
            try:
                result = reject_document(opener, token, doc_id)
                new_statut = result.get("statut", "?") if result else "?"
                print(f"    -> Done. New statut: {new_statut}")
                total_rejected += 1
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                print(f"    -> FAILED: HTTP {e.code} - {err_body}")
            except Exception as e:
                print(f"    -> FAILED: {e}")

    # Final report
    print("\n" + "=" * 60)
    print("CLEANUP REPORT")
    print("=" * 60)
    print(f"Total documents fetched:          {len(docs)}")
    print(f"Already REJETE/ARCHIVE (skipped): {sum(skipped_statuses.values())}")
    print(f"Unique groups:                    {len(groups)}")
    print(f"Groups with duplicates:           {groups_with_dupes}")
    print(f"Documents rejected (cleaned up):  {total_rejected}")
    print("=" * 60)


if __name__ == "__main__":
    main()
