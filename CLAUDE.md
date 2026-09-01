# CLAUDE.md

How to work in this repository. **Practices only.** Every technical decision lives in
`docs/`, and this file may cite one but never restates it — if you find a design decision
written here, it is a bug in this file.

## The four documents, and the rule that keeps them apart

| Document | Question | Owns the namespace |
|---|---|---|
| `docs/cahier-des-charges.md` | **what** | `XXX-NN` — requirements and thresholds |
| `docs/architecture.md` | **how** | `Dn`, `Pn`, block names |
| `docs/plan.md` | **when** | `lot n` |
| `docs/couverture.md` | **where we are** | the statuses, and the coverage count |

**A document may cite another's identifier. It may never define one.** That is what stops
the four from drifting into four copies of each other, and it is checkable by eye: a
paragraph that explains what `D2` *means* belongs to `architecture.md`, wherever you found
it. Section numbers are anchors — never renumber one.

Read all four before designing anything. French in `docs/`, English everywhere else.

```bash
python tools/check_plan_coverage.py              # exits 1 on an orphan requirement or block
python tools/check_plan_coverage.py --self-test  # exits 1 if that check has gone vacuous
```

The second command exists because the first one is a claim like any other. Run it after
changing the shape of the plan's assignment table.

## Two rules that override convenience

**1. Requirements and thresholds are never weakened to obtain a pass.** Fix the system or
record the failure. Do not relax a criterion, narrow the declared scope, or pick an easier
probe. When a verification cannot be run as specified, say so and leave it failing. There is
a worked example of applying this to ourselves in `docs/plan.md` §7.

**2. No field may be neutralised in a comparison unless an A/A run has shown it varies.**
This applies to every comparison you write, not only the oracle.

## Verify before asserting

Never state a third-party API, config field, version, or published figure from memory. Read
the source, cite the URL and the field — or say you do not know. `docs/architecture.md` §13
carries a per-reference verification status: **moving an entry up a level requires quoting
the passage**, not recalling it. Adding a claim without a status is the same error as
inventing one.

The same applies to us: **never say a lot is done, green, or fixed without having run its
exit criterion and read the exit code.** The exit criteria are falsifiable on purpose.

## Where code goes, and how a block is shaped

Seven packages under the repository root, one target directory. `docs/architecture.md` §4
says which is which; do not copy that list here.

- **A block is a function `artefacts -> artefacts`, and no block calls another.** Caching,
  resume, the offline campaign and reproducibility follow from that alone — they are not
  built, they are consequences. A block that imports another block is the defect.
- **Blocks that propose may call a model. Blocks that pronounce may not.** No LLM client
  import under `judge/`. It is grep-checkable on purpose, so grep before you commit.
- **Nothing under the seven packages may know a target.** Everything target-specific lives
  in `targets/<target>/`. A conditional on a target name inside a block is the same defect
  wearing a different hat.
- **Before writing a new block, read `docs/architecture.md` §5.** Three blocks are reused
  several times each; the most common way to add unnecessary code here is to rewrite one of
  them under a new name.

## Before writing code that does not exist elsewhere

Look for a maintained third-party tool first, and cite it. If you find none, the substitute
you looked for and the reason you rejected it go into `docs/architecture.md` §11 **in the
same commit as the custom code** — not afterwards. A discarded tool goes to §12 with its
motive, because an unrecorded rejection gets repeated.

`eslint-disable` and its equivalents hide the problem instead of solving it. Find the shape
of the code that does not trigger the rule.

## Conventions

- Commits: `<type>(<scope>): <description>` — `feat`, `fix`, `chore`, `refactor`, `test`,
  `docs`, `style`, `perf`, `ci`, `build`. A commit that changes a third-party config or
  promotes a reference to verified **cites its source in the message**.
- Stage file by file. Never `--no-verify`, never skip a hook: a failing hook is a cause to
  treat.
- Announce and confirm before anything irreversible — force push, `reset --hard`, remote
  branch deletion, merging or closing a PR.
- Zero comments by default. A comment earns its place only for a non-obvious *why*: a hidden
  constraint, a subtle invariant, a workaround for a named bug. Never "added for ticket X".
- YAGNI. No abstraction, flag, or compatibility shim for a need that does not exist. Three
  similar lines beat a premature abstraction.
