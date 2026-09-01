#!/usr/bin/env python3
"""Check that the plan carries what the other documents define.

Two directions, because a claim in prose cannot be audited:

1. Every blocking socle requirement of `docs/cahier-des-charges.md` is assigned
   to a lot by `docs/plan.md`. An earlier revision dropped CAP-08 -- blocking,
   and described upstream as "not optional" -- and nobody noticed until a review
   read the two documents side by side.
2. Every block named in `docs/architecture.md` is delivered by a lot. Before
   this check existed, 39 of the 50 blocks appeared in no lot at all, including
   `judge/accept`, which produces the eleven ACC acceptance criteria.
3. No requirement is scheduled before a block that carries it. Checking (1) and
   (2) separately let four of these through -- VER-11 was due in lot 1 while
   `judge/accept` arrived in lot 6 -- because each set was complete on its own.

All three are read from the assignment tables, never from prose: citing a
requirement in a rationale is not carrying it.

Exit code is non-zero when any direction fails, so this is usable as a check.
Run `--self-test` to verify the check itself still fails on a dropped
assignment: that mutation is the only evidence the check is not vacuous.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQ = re.compile(r"\b([A-Z]{2,3}-\d{2})\b")
BLOCK = re.compile(r"\b((?:observe|infer|build|run|serve|judge|orchestrate)/[a-z]+)\b")
# A requirement row: | REF | text | Priority |, optionally prefixed by the
# extension marker `o`, whose priority is conditional and never gates delivery.
CDC_ROW = re.compile(
    r"^\|\s*(o\s+)?([A-Z]{2,3}-\d{2})\s*\|(?:[^|]*)\|\s*(Bloquant|Bloquant si retenue|Élevée|Souhaitée)\s*\|",
    re.M,
)


def blocking_requirements(cdc: str) -> set[str]:
    """Blocking socle requirements. Extensions (`o`) do not gate acceptance."""
    return {ref for marker, ref, prio in CDC_ROW.findall(cdc) if prio == "Bloquant" and not marker}


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
        if not (re.match(r"^\d+\.", owner) or "lot" in owner.lower()):
            continue
        if not rest.strip():
            continue
        for name in set(pattern.findall(rest)):
            found.setdefault(name, owner)
    return found


def lot_of(owner: str) -> int | None:
    m = re.search(r"lot (\d+)", owner.lower())
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


def audit(cdc: str, arch: str, plan: str, quiet: bool = False) -> int:
    blocking = blocking_requirements(cdc)
    blocks = architecture_blocks(arch)
    req_owner = carriers(plan, REQ)
    block_owner = carriers(plan, BLOCK)

    orphan_reqs = sorted(blocking - req_owner.keys())
    orphan_blocks = sorted(blocks - block_owner.keys())
    too_early = premature(arch, req_owner, block_owner)

    if not quiet:
        print(f"blocking socle requirements : {len(blocking)}")
        print(f"  assigned to a lot         : {len(blocking & req_owner.keys())}")
        print(f"blocks in architecture.md   : {len(blocks)}")
        print(f"  delivered by a lot        : {len(blocks & block_owner.keys())}")

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

    if too_early and not quiet:
        print(f"\n{len(too_early)} requirement(s) scheduled before a block that carries them:")
        for line in too_early:
            print(f"  {line}")

    if orphan_reqs or orphan_blocks or too_early:
        return 1
    if not quiet:
        print("\nEvery blocking requirement and every block has a carrier,")
        print("and no requirement is due before a block that carries it.")
    return 0


def test_drops_assignment(cdc: str, arch: str, plan: str) -> None:
    """Emptying a lot cell must be caught, in both directions."""
    first_row = next(l for l in plan.splitlines() if l.startswith("| **lot 1"))
    cells = first_row.split("|")
    mutated = plan.replace(first_row, "|  |" + "|".join(cells[2:]))
    assert mutated != plan, "mutation not applied -- the table shape changed"
    assert audit(cdc, arch, mutated, quiet=True) == 1, "a dropped lot cell went unnoticed"

    dropped_block = plan.replace("`judge/accept`", "")
    assert dropped_block != plan, "judge/accept not found -- the table shape changed"
    assert audit(cdc, arch, dropped_block, quiet=True) == 1, "a dropped block went unnoticed"

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
    assert audit(cdc, arch, late_block, quiet=True) == 1, "a premature requirement went unnoticed"

    assert audit(cdc, arch, plan, quiet=True) == 0, "the unmutated plan must pass"
    print("self-test: all three mutations are caught, the unmutated plan passes")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true", help="verify the check still fails on a dropped assignment")
    args = ap.parse_args()

    docs = args.root / "docs"
    cdc = (docs / "cahier-des-charges.md").read_text(encoding="utf-8")
    arch = (docs / "architecture.md").read_text(encoding="utf-8")
    plan = (docs / "plan.md").read_text(encoding="utf-8")

    if args.self_test:
        test_drops_assignment(cdc, arch, plan)
        return 0
    return audit(cdc, arch, plan, quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
