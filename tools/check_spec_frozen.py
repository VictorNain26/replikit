#!/usr/bin/env python3
"""Check the executable specification against its manifest of hashes.

`tests/spec/` holds the requirements as tests. They are not unit tests: they precede the
code and outlive its refactors. The danger they exist to guard against is the one the
literature names for coding agents -- "modifying tests or the verifier" and "overfitting to
visible tests" -- so an instruction not to touch them is not a control.

This is the control. Every spec file has its SHA-256 in `tests/spec/MANIFEST`. A changed
file fails the check until the manifest is updated, which is necessarily a separate,
visible commit. Combined with `.githooks/pre-commit`, which refuses a commit touching both
the spec and a package, a spec change cannot happen quietly.

Correcting the spec stays legitimate. The bar is stated in `tests/spec/README.md`: show that
the test failed for the wrong reason -- not that the code could not satisfy it.

Usage:
    check_spec_frozen.py            verify (exit 1 on drift)
    check_spec_frozen.py --update   rewrite the manifest, for a deliberate correction
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SPEC = RACINE / "tests" / "spec"
MANIFEST = SPEC / "MANIFEST"


def empreintes() -> dict[str, str]:
    return {
        str(f.relative_to(SPEC)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(SPEC.rglob("*"))
        if f.is_file() and f.name != "MANIFEST" and "__pycache__" not in f.parts
    }


def lire_manifeste() -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    lignes = (l.split(maxsplit=1) for l in MANIFEST.read_text(encoding="utf-8").splitlines() if l.strip())
    return {nom: digest for digest, nom in lignes}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--update", action="store_true", help="rewrite the manifest after a deliberate correction")
    args = ap.parse_args()

    courant = empreintes()
    if args.update:
        MANIFEST.write_text("".join(f"{d}  {n}\n" for n, d in courant.items()), encoding="utf-8")
        print(f"manifest rewritten: {len(courant)} spec file(s)")
        print("this must be its own commit, and its message must say why the spec was wrong")
        return 0

    attendu = lire_manifeste()
    if not attendu:
        print("no MANIFEST: run --update once to freeze the current spec", file=sys.stderr)
        return 1

    modifies = sorted(n for n in courant.keys() & attendu.keys() if courant[n] != attendu[n])
    ajoutes = sorted(courant.keys() - attendu.keys())
    retires = sorted(attendu.keys() - courant.keys())

    for nom in modifies:
        print(f"CHANGED  {nom}")
    for nom in ajoutes:
        print(f"ADDED    {nom}")
    for nom in retires:
        print(f"REMOVED  {nom}")

    if modifies or ajoutes or retires:
        print("\nThe frozen specification moved. If that was deliberate, say why the test was")
        print("wrong -- not why the code could not pass it -- and run --update in its own commit.")
        return 1

    print(f"specification frozen: {len(courant)} file(s) unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
