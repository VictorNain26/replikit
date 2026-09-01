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
make check     # document coherence, the checks' own self-test, and the spec freeze
make spec      # the executable specification -- red until the blocks exist
make lot1      # a lot's exit criterion; exits non-zero until the lot is actually held
```

`--self-test` exists because a check is a claim like any other. Run `make check` after
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

## The executable specification is frozen

`tests/spec/` holds the requirements as tests. They are **not** unit tests: unit tests live
beside their block, are disposable, and follow the design. These precede it, and they stay
red until the code satisfies them.

**The rule: a commit may not touch both `tests/spec/` and a package.** `.githooks/pre-commit`
refuses it — enable the hook once with `git config core.hooksPath .githooks`. On top of that,
`tools/check_spec_frozen.py` compares every spec file to its hash in `tests/spec/MANIFEST`.
Neither forbids changing the spec; together they make it impossible to change it *quietly*.

This is not distrust dressed up as process. It is the same mechanism `VER-11` imposes on the
clone generator — the fault set is never exposed to what is being graded — turned on
ourselves, because published work on coding agents lists "modifying tests" and "overfitting
to visible tests" among the shortcuts that get taken when a score is the objective.

**When correcting the spec is legitimate**: when the test failed *for the wrong reason* — not
when the code could not satisfy it. The commit that corrects it carries that demonstration in
its message, and runs `check_spec_frozen.py --update` in that same isolated commit. That
distinction is the whole difference between fixing an error and weakening a criterion.

**Before freezing a new test, watch it fail and read the message.** A test that passes for
the wrong reason is the worst kind, and once frozen it is invisible.

## Where code goes, and how a block is shaped

Seven packages under the repository root, one target directory. `docs/architecture.md` §4
says which is which; do not copy that list here.

- **P1: no block imports another.** `tests/spec/` greps for it and reads the rule strictly —
  no import between modules of the seven packages, same package included. Grep before you
  commit.
- **P3: no LLM client import under `judge/`.** Same grep, same moment.
- **§4: nothing under the seven packages names a target.** Target-specific material lives in
  `targets/<target>/`; a conditional on a target name inside a block is the same defect.
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
