#!/usr/bin/env python3
"""Check that Alembic migrations have a single head (no branching).

Reads migration files directly — no database or alembic install required.
Exit code 0 = single head (safe), 1 = multiple heads (branch conflict).
"""
import pathlib
import re
import sys

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parent.parent / "backend" / "migrations" / "versions"


def main() -> int:
    revs: dict[str, str] = {}  # revision -> down_revision

    for f in sorted(MIGRATIONS_DIR.glob("*.py")):
        txt = f.read_text()
        rid = re.search(r"^revision[\s:]*(?:str\s*)?=\s*['\"]([^'\"]+)", txt, re.MULTILINE)
        did = re.search(r"^down_revision[\s:]*(?:(?:str|Union\[str,\s*None\]|None)\s*)?=\s*['\"]([^'\"]*)", txt, re.MULTILINE)
        if rid:
            revs[rid.group(1)] = did.group(1) if did else ""

    # A "head" is a revision that no other revision points to as its down_revision
    children_of = set(revs.values()) - {""}
    heads = [r for r in revs if r not in children_of]

    print(f"  Migrations: {len(revs)} files, {len(heads)} head(s)")
    for h in heads:
        print(f"    HEAD: {h}")

    if len(heads) != 1:
        print(f"  ERROR: expected 1 head, found {len(heads)} — resolve branch conflict before deploy")
        return 1

    print("  Single head OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
