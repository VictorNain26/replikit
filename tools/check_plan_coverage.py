#!/usr/bin/env python3
"""Check that the four rebuilt documents under docs/ still agree with each other.

A stated count that nothing recounts drifts silently, and a requirement or a step
mentioned in prose is not the same thing as one carried by a lot. This script reads
docs/cahier-des-charges.md, docs/architecture.md, docs/plan.md and docs/couverture.md
from their tables -- never from prose -- and fails if any of the following breaks:

A. every L or O requirement (non-ACC) is assigned to exactly one lot in plan.md §6.
B. every step of architecture.md §4 is delivered by exactly one lot.
C. no requirement is scheduled in a lot earlier than a step architecture.md §5 says
   carries it.
D. every one of the 73 requirements has exactly one row in architecture.md §5.
E. couverture.md §1: each family's statuses sum to its total, each total matches the
   cahier's count for that family, the grand total matches, and every family has a row.
F. every step cited in architecture.md §5 or in plan.md §6's table is declared in
   architecture.md §4's step table.
G. plan.md §5's per-lot `*Exigences* :` prose matches that lot's row in §6's table.
H. plan.md §5's per-lot `*Étapes* :` prose matches that lot's row in §6's table.

Run --self-test to verify each of these still fails on a mutated copy of the documents.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

REQ = re.compile(r"\b([A-Z]{2,3}-\d{2})\b")
BLOCK = re.compile(r"\b((?:observe|infer|build|run|serve|judge|orchestrate)/[a-z]+)\b")

# A requirement row of the cahier's eight families: | REF | text | source | mesure | standard | rang |,
# optionally prefixed by the extension marker `o`. Restricted to a single line: a
# malformed row must not swallow the next one.
CDC_ROW = re.compile(
    r"^\|\s*(o\s+)?([A-Z]{2,3}-\d{2})\s*\|(?:[^|\n]*\|){4}\s*([^|\n]+?)\s*\|\s*$",
    re.M,
)
# An ACC row has no rank: | ACC-NN | condition | source | seuil |.
ACC_ROW = re.compile(r"^\|\s*(ACC-\d{2})\s*\|(?:[^|\n]*\|){2}\s*[^|\n]+\|\s*$", re.M)

# A step cell of architecture.md §4: | `paquet/etape` | ...
STEP_CELL = re.compile(r"^\|\s*`([a-z]+/[a-z]+)`\s*\|", re.M)
# Any row of architecture.md §5 whose first cell is a requirement, ACC included.
ARCH5_ROW = re.compile(r"^\|\s*(?:o\s+)?([A-Z]{2,3}-\d{2})\s*\|", re.M)

# | 6. Capture (CAP) | done | partial | absent | total | lot |
COV_ROW = re.compile(r"^\|\s*\d+\.\s*([^|]*?)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", re.M)
COV_TOTAL = re.compile(r"^\|\s*\*\*Total\*\*\s*\|[^|]*\|[^|]*\|[^|]*\|\s*\*\*(\d+)\*\*\s*\|", re.M)


def section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]


def requirement_ranks(cdc: str) -> dict[str, str]:
    """Rank of every non-ACC requirement, taken as the first letter of the Rang cell."""
    return {ref: rang.strip()[0] for _marker, ref, rang in CDC_ROW.findall(cdc)}


def all_requirements(cdc: str) -> list[str]:
    refs = [ref for _marker, ref, _rang in CDC_ROW.findall(cdc)]
    refs += ACC_ROW.findall(cdc)
    return refs


def architecture_steps(arch: str) -> set[str]:
    return set(STEP_CELL.findall(section(arch, "## 4. Les étapes", "## 5.")))


def architecture_section5(arch: str) -> str:
    return section(arch, "## 5.", "## 6.")


def architecture_rows(arch: str) -> Counter[str]:
    return Counter(ARCH5_ROW.findall(architecture_section5(arch)))


def architecture_req_steps(arch: str) -> dict[str, set[str]]:
    """Steps §5 says carry each requirement. Rows with fewer than 4 cells (the ACC
    table has 3) have no step column and are skipped."""
    mapping: dict[str, set[str]] = {}
    for line in architecture_section5(arch).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        m = re.match(r"(?:o\s+)?([A-Z]{2,3}-\d{2})", cells[0])
        if not m:
            continue
        mapping[m.group(1)] = set(BLOCK.findall(cells[1]))
    return mapping


def lot_of(owner: str) -> int | None:
    m = re.search(r"\blot (\d+)\b", owner.lower())
    return int(m.group(1)) if m else None


def carriers(plan: str, pattern: re.Pattern[str]) -> dict[str, list[str]]:
    """Names assigned by every row of plan.md §6 whose first cell names a lot.

    A row whose first cell is itself a list of names is NOT a carrier -- that shape let
    a row with an empty lot column pass as covered, which this check exists to catch.
    A name found in more than one carrier row is reported as such, not silently kept
    once.
    """
    found: dict[str, list[str]] = {}
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
            found.setdefault(name, []).append(owner)
    return found


def unassigned_or_duplicated(names: set[str], owners: dict[str, list[str]]) -> list[str]:
    out = []
    for name in sorted(names):
        n = len(owners.get(name, []))
        if n == 0:
            out.append(f"{name}: carried by no lot")
        elif n > 1:
            out.append(f"{name}: carried by {n} lots ({', '.join(owners[name])})")
    return out


def premature(req_owners: dict[str, list[str]], step_owners: dict[str, list[str]], req_steps5: dict[str, set[str]], steps4: set[str]) -> list[str]:
    out: list[str] = []
    for req, owners in req_owners.items():
        if len(owners) != 1:
            continue
        req_lot = lot_of(owners[0])
        if req_lot is None:
            continue
        for step in sorted(req_steps5.get(req, set()) & steps4):
            step_owner = step_owners.get(step, [])
            if len(step_owner) != 1:
                continue
            step_lot = lot_of(step_owner[0])
            if step_lot is not None and step_lot > req_lot:
                out.append(f"{req} is due in lot {req_lot} but {step} arrives in lot {step_lot}")
    return sorted(out)


def not_one_row_in_architecture(all_refs: list[str], rows: Counter[str]) -> list[str]:
    return sorted(f"{ref}: {rows[ref]} row(s) in architecture.md §5" for ref in all_refs if rows[ref] != 1)


def family_of(label: str) -> str | None:
    m = re.search(r"\(([A-Z]{2,3})\)", label)
    if m:
        return m.group(1)
    tokens = re.findall(r"\b([A-Z]{2,3})\b", label)
    return tokens[-1] if tokens else None


def couverture_issues(reqs: list[str], cov: str) -> list[str]:
    out: list[str] = []
    per_family = Counter(ref.split("-")[0] for ref in reqs)
    seen: set[str] = set()
    for label, done, partial, absent, total in COV_ROW.findall(cov):
        fam = family_of(label)
        if fam is None:
            out.append(f"couverture §1: no family code in row '{label}'")
            continue
        seen.add(fam)
        if int(done) + int(partial) + int(absent) != int(total):
            out.append(f"couverture §1: {fam} statuses sum to {int(done) + int(partial) + int(absent)}, not {total}")
        if int(total) != per_family.get(fam, 0):
            out.append(f"couverture §1 states {total} for {fam}, the cahier holds {per_family.get(fam, 0)}")
    for fam in sorted(per_family.keys() - seen):
        out.append(f"couverture §1 has no row for {fam}")
    m = COV_TOTAL.search(cov)
    if not m:
        out.append("couverture §1: no Total row")
    elif int(m.group(1)) != len(reqs):
        out.append(f"couverture §1 states {m.group(1)} in total, the cahier holds {len(reqs)}")
    return out


LOT_HEADING = re.compile(r"^### Lot (\d+)", re.M)


def plan_section5(plan: str) -> str:
    return section(plan, "## 5. Lots", "## 6.")


def plan_section6(plan: str) -> str:
    return section(plan, "## 6.", "## 7.")


def cited_steps(arch: str, plan: str) -> dict[str, set[str]]:
    """Every step name found in architecture.md §5 or plan.md §6, with its source(s)."""
    sources: dict[str, set[str]] = {}
    for step in BLOCK.findall(architecture_section5(arch)):
        sources.setdefault(step, set()).add("architecture §5")
    for step in BLOCK.findall(plan_section6(plan)):
        sources.setdefault(step, set()).add("plan §6")
    return sources


def undeclared_steps(arch: str, plan: str, steps4: set[str]) -> list[str]:
    sources = cited_steps(arch, plan)
    out = []
    for step in sorted(sources):
        if step in steps4:
            continue
        for src in sorted(sources[step]):
            out.append(f"{step}: cited in {src} but not declared in architecture §4")
    return out


def prose_block(body: str, label: str) -> str:
    """Text after `*label* :` up to the next blank line -- the wrap point every lot uses."""
    m = re.search(rf"\*{label}\*\s*:\s*(.*?)(?:\n\s*\n|\Z)", body, re.S)
    return m.group(1) if m else ""


def lot_prose(plan: str) -> dict[int, tuple[set[str], set[str]]]:
    """Per-lot (steps, requirements) named in §5's `*Étapes*` and `*Exigences*` prose."""
    text = plan_section5(plan)
    headings = list(LOT_HEADING.finditer(text))
    out: dict[int, tuple[set[str], set[str]]] = {}
    for i, m in enumerate(headings):
        lot = int(m.group(1))
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[m.end() : end]
        steps = set(BLOCK.findall(prose_block(body, "Étapes")))
        reqs = set(REQ.findall(prose_block(body, "Exigences")))
        out[lot] = (steps, reqs)
    return out


def lot_table_sets(plan: str) -> dict[int, tuple[set[str], set[str]]]:
    """Per-lot (steps, requirements) named in §6's table row, keyed the same way as lot_prose."""
    out: dict[int, tuple[set[str], set[str]]] = {}
    for line in plan.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0].startswith("---"):
            continue
        lot = lot_of(cells[0])
        if lot is None:
            continue
        rest = " ".join(cells[1:])
        out[lot] = (set(BLOCK.findall(rest)), set(REQ.findall(rest)))
    return out


def prose_vs_table(plan: str, index: int) -> list[str]:
    """index 0 compares steps (check H), index 1 compares requirements (check G)."""
    prose = lot_prose(plan)
    table = lot_table_sets(plan)
    out = []
    for lot in sorted(prose):
        named_prose = prose[lot][index]
        named_table = table.get(lot, (set(), set()))[index]
        missing_from_table = sorted(named_prose - named_table)
        missing_from_prose = sorted(named_table - named_prose)
        if not missing_from_table and not missing_from_prose:
            continue
        parts = []
        if missing_from_table:
            parts.append(f"in prose but not in table: {', '.join(missing_from_table)}")
        if missing_from_prose:
            parts.append(f"in table but not in prose: {', '.join(missing_from_prose)}")
        out.append(f"lot {lot}: " + "; ".join(parts))
    return out


def audit(cdc: str, arch: str, plan: str, cov: str, quiet: bool = False) -> int:
    reqs = all_requirements(cdc)
    ranks = requirement_ranks(cdc)
    lo_reqs = {ref for ref, rank in ranks.items() if rank in ("L", "O")}

    steps4 = architecture_steps(arch)
    arch_rows = architecture_rows(arch)
    req_steps5 = architecture_req_steps(arch)

    req_owners = carriers(plan, REQ)
    step_owners = carriers(plan, BLOCK)

    unassigned_reqs = unassigned_or_duplicated(lo_reqs, req_owners)
    undelivered_steps = unassigned_or_duplicated(steps4, step_owners)
    too_early = premature(req_owners, step_owners, req_steps5, steps4)
    unmapped = not_one_row_in_architecture(reqs, arch_rows)
    miscounted = couverture_issues(reqs, cov)
    stray_steps = undeclared_steps(arch, plan, steps4)
    req_prose_mismatch = prose_vs_table(plan, 1)
    step_prose_mismatch = prose_vs_table(plan, 0)

    if not quiet:
        print(f"requirements in the cahier    : {len(reqs)}")
        print(f"  with one row in §5          : {len(reqs) - len(unmapped)}")
        print(f"L or O requirements            : {len(lo_reqs)}")
        print(f"  assigned to exactly one lot : {len(lo_reqs) - len(unassigned_reqs)}")
        print(f"steps in architecture.md §4    : {len(steps4)}")
        print(f"  delivered by exactly one lot: {len(steps4) - len(undelivered_steps)}")

    for title, lines in (
        ("L/O requirement(s) not carried by exactly one lot", unassigned_reqs),
        ("step(s) of architecture.md §4 not delivered by exactly one lot", undelivered_steps),
        ("requirement(s) scheduled before a step that carries them", too_early),
        ("requirement(s) without exactly one row in architecture.md §5", unmapped),
        ("stated count(s) that couverture.md §1 contradicts", miscounted),
        ("step(s) cited but not declared in architecture.md §4", stray_steps),
        ("lot(s) where §5's requirement prose disagrees with §6's table", req_prose_mismatch),
        ("lot(s) where §5's step prose disagrees with §6's table", step_prose_mismatch),
    ):
        if lines and not quiet:
            print(f"\n{len(lines)} {title}:")
            for line in lines:
                print(f"  {line}")

    if (
        unassigned_reqs
        or undelivered_steps
        or too_early
        or unmapped
        or miscounted
        or stray_steps
        or req_prose_mismatch
        or step_prose_mismatch
    ):
        return 1
    if not quiet:
        print("\nEvery L or O requirement and every step has exactly one carrier, no requirement is")
        print("due before a step that carries it, architecture.md §5 maps each requirement once,")
        print("and couverture.md §1 matches the cahier's tables.")
    return 0


def test_checks(cdc: str, arch: str, plan: str, cov: str) -> None:
    """Each kind of drift must be caught."""
    lot1_row = next(l for l in plan.splitlines() if l.startswith("| **lot 1"))
    cells = lot1_row.split("|")
    mutated = plan.replace(lot1_row, "|  |" + "|".join(cells[2:]), 1)
    assert mutated != plan, "mutation not applied -- the table shape changed"
    assert audit(cdc, arch, mutated, cov, quiet=True) == 1, "a blanked lot 1 cell went unnoticed"

    lot2_row = next(l for l in plan.splitlines() if l.startswith("| **lot 2"))
    dropped_line = lot2_row.replace(" `judge/report`", "", 1)
    assert dropped_line != lot2_row, "judge/report not found in the lot 2 row -- the table shape changed"
    dropped_plan = plan.replace(lot2_row, dropped_line, 1)
    assert audit(cdc, arch, dropped_plan, cov, quiet=True) == 1, "a dropped step went unnoticed"

    lot1_row2 = next(l for l in plan.splitlines() if l.startswith("| **lot 1"))
    lot1_without_diff = lot1_row2.replace(" `judge/diff`", "", 1)
    assert lot1_without_diff != lot1_row2, "judge/diff not found in the lot 1 row -- the table shape changed"
    lot5_row = next(l for l in plan.splitlines() if l.startswith("| **lot 5"))
    lot5_with_diff = lot5_row.replace("`observe/agent`", "`observe/agent` `judge/diff`", 1)
    assert lot5_with_diff != lot5_row, "observe/agent not found in the lot 5 row -- the table shape changed"
    late_step = plan.replace(lot1_row2, lot1_without_diff, 1).replace(lot5_row, lot5_with_diff, 1)
    assert audit(cdc, arch, late_step, cov, quiet=True) == 1, "a premature requirement went unnoticed"

    cap05_row = next(l for l in arch.splitlines() if l.startswith("| CAP-05 "))
    no_row = arch.replace(cap05_row + "\n", "", 1)
    assert no_row != arch, "CAP-05 row not found -- the table shape changed"
    assert audit(cdc, no_row, plan, cov, quiet=True) == 1, "a requirement without a §5 row went unnoticed"

    cap_line = next(l for l in cov.splitlines() if "(CAP)" in l)
    m = COV_ROW.search(cap_line)
    assert m, "the couverture CAP row was not found -- the table shape changed"
    start, end = m.span(4)
    bad_cap_line = cap_line[:start] + str(int(m.group(4)) - 1) + cap_line[end:]
    assert bad_cap_line != cap_line, "the couverture mutation was not applied"
    bad_sum_cov = cov.replace(cap_line, bad_cap_line, 1)
    assert audit(cdc, arch, plan, bad_sum_cov, quiet=True) == 1, "a wrong couverture sum went unnoticed"

    mt = COV_TOTAL.search(cov)
    assert mt, "the couverture Total row was not found"
    bad_total_cov = cov[: mt.start(1)] + "72" + cov[mt.end(1) :]
    assert bad_total_cov != cov, "the Total mutation was not applied"
    assert audit(cdc, arch, plan, bad_total_cov, quiet=True) == 1, "a wrong couverture total went unnoticed"

    invented = plan.replace(lot1_row, lot1_row.replace("`judge/diff`", "`judge/diff` `judge/foo`", 1), 1)
    assert invented != plan, "the invented-step mutation was not applied"
    assert audit(cdc, arch, invented, cov, quiet=True) == 1, "a step absent from architecture §4 went unnoticed"

    prose = prose_block(plan_section5(plan).split("### Lot 2", 1)[0], "Exigences")
    assert "`CAP-01`" in prose, "CAP-01 not found in the lot 1 prose -- the shape changed"
    prose_drift = plan.replace(prose, prose.replace("`CAP-01`, ", "", 1), 1)
    assert prose_drift != plan, "the prose mutation was not applied"
    assert audit(cdc, arch, prose_drift, cov, quiet=True) == 1, "a requirement dropped from the lot prose went unnoticed"

    step_prose = prose_block(plan_section5(plan).split("### Lot 2", 1)[0], "Étapes")
    assert "`observe/aa`" in step_prose, "observe/aa not found in the lot 1 prose -- the shape changed"
    step_drift = plan.replace(step_prose, step_prose.replace("`observe/aa`, ", "", 1), 1)
    assert step_drift != plan, "the step prose mutation was not applied"
    assert audit(cdc, arch, step_drift, cov, quiet=True) == 1, "a step dropped from the lot prose went unnoticed"

    duplicated = plan.replace(lot2_row, lot2_row.replace("`CAP-06`", "`CAP-06`, `CAP-01`", 1), 1)
    assert duplicated != plan, "the duplication mutation was not applied"
    assert audit(cdc, arch, duplicated, cov, quiet=True) == 1, "a requirement carried by two lots went unnoticed"

    assert audit(cdc, arch, plan, cov, quiet=True) == 0, "the unmutated documents must pass"
    print("self-test: all ten mutations are caught, the unmutated documents pass")


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
        test_checks(cdc, arch, plan, cov)
        return 0
    return audit(cdc, arch, plan, cov, quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
