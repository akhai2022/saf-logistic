#!/usr/bin/env python3
"""
Push vehicle registration dates (date_premiere_immatriculation) to the production API.

This script should be run AFTER the backend fix for date_premiere_immatriculation
has been deployed (the fix in masterdata/router.py that resolves the 500 error
when sending a date field via PUT).

It first tests a single vehicle update to confirm the fix is live. If the test
fails with HTTP 500, it aborts early.

Usage:
  python integration/push_vehicle_dates.py
"""
import json
import sys
import urllib.error
import urllib.request

API = "https://api-saf.dataforgeai.fr"
SAF_TENANT = "10000000-0000-0000-0000-000000000001"

# Registration dates from certificat d'immatriculation
VEHICLE_DATES = {
    "EC-521-HX": "2016-05-23",
    "FF-687-FS": "2019-04-05",
    "DT-392-ED": "2015-07-09",
    "EB-007-HK": "2016-04-14",
    "DX-485-WV": "2008-05-30",
    "CT-529-GA": "2006-08-01",
    "CB-631-JN": "2012-02-13",
    "CH-398-HL": "2012-07-04",
    "BL-336-PV": "2006-11-06",
    "BF-304-TQ": "2011-01-05",
    "AW-639-SE": "2010-07-12",
    "AK-768-JX": "2010-01-25",
    "AD-815-GW": "2009-10-08",
    "AC-013-YA": "2009-05-03",
}


# ── Redirect-following opener (urllib doesn't follow redirects for PUT/POST) ──

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


def login():
    data = json.dumps({
        "email": "admin@saf-logistique.fr",
        "password": "SafAdmin2026!",
        "tenant_id": SAF_TENANT,
    }).encode()
    req = urllib.request.Request(
        f"{API}/v1/auth/login", data=data,
        headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode())["access_token"]


def api_get(token, path):
    req = urllib.request.Request(f"{API}{path}", headers={
        "Authorization": f"Bearer {token}", "X-Tenant-ID": SAF_TENANT})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())


def api_put(token, path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{API}{path}", data=data, method="PUT", headers={
        "Authorization": f"Bearer {token}", "X-Tenant-ID": SAF_TENANT,
        "Content-Type": "application/json"})
    resp = _opener.open(req, timeout=30)
    return json.loads(resp.read().decode())


def main():
    print("Logging in...")
    token = login()
    print("OK\n")

    # ── Load all vehicles and build immat -> vehicle map ──
    print("Fetching vehicles...")
    vehicles = api_get(token, "/v1/masterdata/vehicles?limit=50")
    items = vehicles.get("items", vehicles) if isinstance(vehicles, dict) else vehicles
    vehicle_map = {}
    for v in items:
        immat = v.get("immatriculation") or v.get("plate_number", "")
        if immat:
            vehicle_map[immat] = v
    print(f"Found {len(vehicle_map)} vehicles\n")

    # ── Smoke test: try updating one vehicle with the date field ──
    test_immat = "EC-521-HX"
    test_date = VEHICLE_DATES[test_immat]
    test_vehicle = vehicle_map.get(test_immat)
    if not test_vehicle:
        print(f"ABORT: test vehicle {test_immat} not found in system")
        sys.exit(1)

    print(f"Smoke test: PUT {test_immat} with date_premiere_immatriculation={test_date}...")
    try:
        api_put(token, f"/v1/masterdata/vehicles/{test_vehicle['id']}", {
            "immatriculation": test_immat,
            "date_premiere_immatriculation": test_date,
        })
        print("OK - fix is deployed!\n")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if hasattr(e, "read") else str(e)
        if e.code == 500:
            print(f"ABORT: got HTTP 500 - the backend fix has NOT been deployed yet.")
            print(f"       Deploy the fix first, then re-run this script.")
            print(f"       Response: {body[:300]}")
            sys.exit(1)
        else:
            print(f"ABORT: unexpected HTTP {e.code}: {body[:300]}")
            sys.exit(1)

    # ── Push all dates ──
    print("Pushing registration dates for all vehicles...")
    ok = 0
    skipped = 0
    errors = 0

    for immat, reg_date in VEHICLE_DATES.items():
        vehicle = vehicle_map.get(immat)
        if not vehicle:
            print(f"  SKIP {immat:12s} - not found in system")
            skipped += 1
            continue

        # Skip if already set to the correct value
        existing_date = vehicle.get("date_premiere_immatriculation") or vehicle.get("first_registration")
        if existing_date and str(existing_date)[:10] == reg_date:
            print(f"  SKIP {immat:12s} - already has {reg_date}")
            skipped += 1
            continue

        try:
            api_put(token, f"/v1/masterdata/vehicles/{vehicle['id']}", {
                "immatriculation": immat,
                "date_premiere_immatriculation": reg_date,
            })
            print(f"  OK   {immat:12s} -> {reg_date}")
            ok += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode() if hasattr(e, "read") else str(e)
            print(f"  FAIL {immat:12s} - HTTP {e.code}: {body[:200]}")
            errors += 1
        except Exception as e:
            print(f"  FAIL {immat:12s} - {e}")
            errors += 1

    # ── Summary ──
    print(f"\nDone: {ok} updated, {skipped} skipped, {errors} errors")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
