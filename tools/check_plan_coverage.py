#!/usr/bin/env python3
"""Check that the four documents carry what each of them claims.

Every direction below exists because a claim in prose cannot be audited:

1. Every blocking socle requirement of `docs/cahier-des-charges.md` is assigned
   to a lot by `docs/plan.md`. An earlier revision dropped CAP-08 -- blocking,
   and described upstream as "not optional" -- and nobody noticed until a review
   read the two documents side by side.
2. Every block named in `docs/architecture.md` is delivered by a lot. Before
   this check existed, 39 of the blocks appeared in no lot at all, including
   `judge/accept`, which produces the eleven ACC acceptance criteria.
3. No requirement is scheduled before a block that carries it. Checking (1) and
   (2) separately let four of these through -- VER-11 was due in lot 1 while
   `judge/accept` arrived in lot 6 -- because each set was complete on its own.
4. Every requirement has exactly one row in `docs/architecture.md` §9, which
   claims "une ligne par exigence".
5. The counts the documents state -- the cahier's "87 socle, 4 extensions, 64
   bloquantes" line, and the per-family rows of `docs/couverture.md`, whose
   statuses must sum to their total and whose total must equal the cahier's --
   equal what the cahier's tables actually contain. The audit of 2026-09-01
   recounted them by hand; a stated count that nothing recounts drifts silently.

All of them are read from tables, never from prose: citing a requirement in a
rationale is not carrying it.

Exit code is non-zero when any direction fails, so this is usable as a check.
Run `--self-test` to verify the check itself still fails on each kind of
drift: those mutations are the only evidence the check is not vacuous.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REQ = re.compile(r"\b([A-Z]{2,3}-\d{2})\b")
BLOCK = re.compile(r"\b((?:observe|infer|build|run|serve|judge|orchestrate)/[a-z]+)\b")
# A requirement row: | REF | text | Priority |, optionally prefixed by the
# extension marker `o`, whose priority is conditional and never gates delivery.
CDC_ROW = re.compile(
    r"^\|\s*(o\s+)?([A-Z]{2,3}-\d{2})\s*\|(?:[^|]*)\|\s*(Bloquant|Bloquant si retenue|Élevée|Souhaitée)\s*\|",
    re.M,
)
# Any requirement row, ACC criteria included (their third cell is a threshold).
ANY_ROW = re.compile(r"^\|\s*(?:o\s+)?([A-Z]{2,3}-\d{2})\s*\|", re.M)
CDC_COUNT = re.compile(
    r"Décompte : (\d+) exigences de socle, (\d+) extensions.*?Dont (\d+) exigences de socle bloquantes"
)
# | 4. Capture (CAP) | ✅ | 🟡 | ❌ | Total | lot |
COV_ROW = re.compile(r"^\|\s*\d+\.\s*([^|]*?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", re.M)
COV_TOTAL = re.compile(r"^\|\s*\*\*Total\*\*\s*\|[^|]*\|[^|]*\|[^|]*\|\s*\*\*(\d+)\*\*\s*\|", re.M)


def blocking_requirements(cdc: str) -> set[str]:
    """Blocking socle requirements. Extensions (`o`) do not gate acceptance."""
    return {ref for marker, ref, prio in CDC_ROW.findall(cdc) if prio == "Bloquant" and not marker}


def all_requirements(cdc: str) -> list[str]:
    return ANY_ROW.findall(cdc)


def architecture_blocks(arch: str) -> set[str]:
    return set(BLOCK.findall(arch))


def carriers(plan: str, pattern: re.Pattern[str]) -> dict[str, str]:
    """Names assigned by a table row whose FIRST cell names a lot.

    The first cell is the carrier; the names come from the rest of the row. A row
    whose first cell is itself a list of names is NOT a carrier -- that shape let
    a row with an empty lot column pass as covered, which is the failure this
    check exists to catch. Verified by `--self-test`.
    """
    found: dict[str, str] = {}
    for line in plan.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0].startswith("---"):
            continue
        owner, rest = cells[0], " ".join(cells[1:])
        if lot_of(owner) is None:
            continue
        if not rest.strip():
            continue
        for name in set(pattern.findall(rest)):
            found.setdefault(name, owner)
    return found


def lot_of(owner: str) -> int | None:
    m = re.search(r"\blot (\d+)\b", owner.lower())
    return int(m.group(1)) if m else None


def premature(arch: str, req_owner: dict[str, str], block_owner: dict[str, str]) -> list[str]:
    """Requirements due before a block that architecture.md says carries them.

    Reads the coverage rows of architecture.md §9, whose shape is
    | REQ | blocks | rationale |, and compares lot numbers on both sides.
    """
    out: list[str] = []
    for line in arch.splitlines():
        if not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        head = REQ.match(cells[0].removeprefix("o "))
        if not head or head.group(1) not in req_owner:
            continue
        req = head.group(1)
        req_lot = lot_of(req_owner[req])
        if req_lot is None:
            continue
        for block in sorted(set(BLOCK.findall(cells[1]))):
            block_lot = lot_of(block_owner.get(block, ""))
            if block_lot is not None and block_lot > req_lot:
                out.append(f"{req} is due in lot {req_lot} but {block} arrives in lot {block_lot}")
    return sorted(set(out))


def not_one_row_in_architecture(cdc: str, arch: str) -> list[str]:
    """architecture.md §9 claims one row per requirement. Count them."""
    rows = Counter(all_requirements(arch))
    return sorted(f"{ref}: {rows[ref]} row(s) in architecture.md" for ref in all_requirements(cdc) if rows[ref] != 1)


def stated_counts_wrong(cdc: str, cov: str) -> list[str]:
    """The counts the documents state versus the cahier's tables."""
    out: list[str] = []
    reqs = all_requirements(cdc)
    rows = CDC_ROW.findall(cdc)
    socle = len(reqs) - sum(1 for marker, _, _ in rows if marker)
    extensions = sum(1 for marker, _, _ in rows if marker)
    blocking = len(blocking_requirements(cdc))

    m = CDC_COUNT.search(cdc)
    if not m:
        out.append("cahier §3: the 'Décompte' line was not found")
    else:
        for label, stated, actual in (("socle", m.group(1), socle), ("extensions", m.group(2), extensions), ("bloquantes", m.group(3), blocking)):
            if int(stated) != actual:
                out.append(f"cahier §3 states {stated} {label}, the tables hold {actual}")

    per_family = Counter(ref.split("-")[0] for ref in reqs)
    seen: set[str] = set()
    for label, done, partial, absent, total in COV_ROW.findall(cov):
        fam = re.search(r"\b([A-Z]{2,3})\b", label)
        if not fam:
            out.append(f"couverture §1: no family code in row '{label}'")
            continue
        seen.add(fam.group(1))
        if int(done) + int(partial) + int(absent) != int(total):
            out.append(f"couverture §1: {fam.group(1)} statuses sum to {int(done) + int(partial) + int(absent)}, not {total}")
        if int(total) != per_family[fam.group(1)]:
            out.append(f"couverture §1 states {total} for {fam.group(1)}, the cahier holds {per_family[fam.group(1)]}")
    for fam in sorted(per_family.keys() - seen):
        out.append(f"couverture §1 has no row for {fam}")
    m = COV_TOTAL.search(cov)
    if not m:
        out.append("couverture §1: no Total row")
    elif int(m.group(1)) != len(reqs):
        out.append(f"couverture §1 states {m.group(1)} in total, the cahier holds {len(reqs)}")
    return out


def audit(cdc: str, arch: str, plan: str, cov: str, quiet: bool = False) -> int:
    blocking = blocking_requirements(cdc)
    blocks = architecture_blocks(arch)
    req_owner = carriers(plan, REQ)
    block_owner = carriers(plan, BLOCK)

    orphan_reqs = sorted(blocking - req_owner.keys())
    orphan_blocks = sorted(blocks - block_owner.keys())
    too_early = premature(arch, req_owner, block_owner)
    unmapped = not_one_row_in_architecture(cdc, arch)
    miscounted = stated_counts_wrong(cdc, cov)

    if not quiet:
        print(f"requirements in the cahier    : {len(all_requirements(cdc))}")
        print(f"  with one row in architecture: {len(all_requirements(cdc)) - len(unmapped)}")
        print(f"blocking socle requirements   : {len(blocking)}")
        print(f"  assigned to a lot           : {len(blocking & req_owner.keys())}")
        print(f"blocks in architecture.md     : {len(blocks)}")
        print(f"  delivered by a lot          : {len(blocks & block_owner.keys())}")

    for label, orphans, source in (
        ("blocking requirement", orphan_reqs, plan),
        ("architecture block", orphan_blocks, plan),
    ):
        if not orphans or quiet:
            continue
        print(f"\n{len(orphans)} {label}(s) with no carrier:")
        for name in orphans:
            note = " (mentioned in prose only -- a mention is not a plan)" if name in source else ""
            print(f"  {name}{note}")

    for title, lines in (
        ("requirement(s) scheduled before a block that carries them", too_early),
        ("requirement(s) without exactly one row in architecture.md §9", unmapped),
        ("stated count(s) that the tables contradict", miscounted),
    ):
        if lines and not quiet:
            print(f"\n{len(lines)} {title}:")
            for line in lines:
                print(f"  {line}")

    if orphan_reqs or orphan_blocks or too_early or unmapped or miscounted:
        return 1
    if not quiet:
        print("\nEvery blocking requirement and every block has a carrier, no requirement is")
        print("due before a block that carries it, architecture.md maps each requirement once,")
        print("and every stated count matches the tables.")
    return 0


def test_drops_assignment(cdc: str, arch: str, plan: str, cov: str) -> None:
    """Each kind of drift must be caught."""
    first_row = next(l for l in plan.splitlines() if l.startswith("| **lot 1"))
    cells = first_row.split("|")
    mutated = plan.replace(first_row, "|  |" + "|".join(cells[2:]))
    assert mutated != plan, "mutation not applied -- the table shape changed"
    assert audit(cdc, arch, mutated, cov, quiet=True) == 1, "a dropped lot cell went unnoticed"

    dropped_block = plan.replace("`judge/accept`", "")
    assert dropped_block != plan, "judge/accept not found -- the table shape changed"
    assert audit(cdc, arch, dropped_block, cov, quiet=True) == 1, "a dropped block went unnoticed"

    # move judge/diff from lot 1 to lot 6 in the assignment table: VER-01 is then
    # scheduled before a block that architecture.md says carries it
    rows = []
    moved = False
    for line in plan.splitlines(keepends=True):
        if line.startswith("| **lot 1") and "`judge/diff`" in line:
            line, moved = line.replace(" `judge/diff`", "", 1), True
        elif line.startswith("| **lot 6"):
            line = line.replace("`judge/accept`", "`judge/accept` `judge/diff`", 1)
        rows.append(line)
    late_block = "".join(rows)
    assert moved, "judge/diff not found in the lot 1 row -- the table shape changed"
    assert audit(cdc, arch, late_block, cov, quiet=True) == 1, "a premature requirement went unnoticed"

    cap05_row = next(l for l in arch.splitlines() if l.startswith("| CAP-05 "))
    no_row = arch.replace(cap05_row + "\n", "", 1)
    assert no_row != arch, "CAP-05 row not found -- the table shape changed"
    assert audit(cdc, no_row, plan, cov, quiet=True) == 1, "a requirement without a §9 row went unnoticed"

    m = CDC_COUNT.search(cdc)
    assert m, "the 'Décompte' line was not found"
    miscount = cdc.replace(m.group(0), m.group(0).replace(m.group(3), str(int(m.group(3)) - 1), 1), 1)
    assert miscount != cdc, "the count mutation was not applied"
    assert audit(miscount, arch, plan, cov, quiet=True) == 1, "a wrong stated count went unnoticed"

    cap_row = next(l for l in cov.splitlines() if "(CAP)" in l)
    miscov = cov.replace(cap_row, cap_row.replace("| 11 |", "| 10 |", 1), 1)
    assert miscov != cov, "the couverture mutation was not applied -- the table shape changed"
    assert audit(cdc, arch, plan, miscov, quiet=True) == 1, "a wrong couverture total went unnoticed"

    assert audit(cdc, arch, plan, cov, quiet=True) == 0, "the unmutated documents must pass"
    print("self-test: all six mutations are caught, the unmutated documents pass")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="verify the check still fails on each kind of drift")
    args = ap.parse_args()

    docs = args.root / "docs"
    cdc = (docs / "cahier-des-charges.md").read_text(encoding="utf-8")
    arch = (docs / "architecture.md").read_text(encoding="utf-8")
    plan = (docs / "plan.md").read_text(encoding="utf-8")
    cov = (docs / "couverture.md").read_text(encoding="utf-8")

    if args.self_test:
        test_drops_assignment(cdc, arch, plan, cov)
        return 0
    return audit(cdc, arch, plan, cov, quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
