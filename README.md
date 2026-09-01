# replikit

A demonstrator of the toolchain a *Replication Engineer* needs: take a third-party web
application observable only from the outside — or its source when it is open — produce a
runnable, resettable clone, and **prove** the clone is behaviourally indistinguishable from
the original on a declared scope.

The hard part is not the clone. It is the oracle — deciding, reproducibly and
automatically, that two systems behave identically for the same sequence of inputs. The
published state of the art clones real websites into environments with verifiable *task*
rewards (VeriEnv, InfiniteWeb) and describes no protocol of fidelity to the original. That
gap is what this repository is about.

## Status

**Documentation and an executable specification. No product code yet.**
`docs/couverture.md` holds the count, and it is the only place that number lives.

```bash
make check   # the four documents agree, the checker's self-test bites, the spec is frozen
make spec    # the executable specification -- red until the steps exist
make lot1    # a lot's exit criterion; exits non-zero until the lot is actually held
```

## The four documents

Each answers one question, owns one namespace of identifiers, and repeats none of the
others. Read them in this order.

| Document | Question |
|---|---|
| `docs/cahier-des-charges.md` | **What** — 73 requirements, each quoting the sentence of the reference brief it comes from, each naming what it measures and the standard its output follows; no invented threshold |
| `docs/architecture.md` | **How** — nine decisions, 35 steps, one verified tool per requirement, what stays home-made and the substitute that was looked for, what is unresolved, what was discarded and why |
| `docs/plan.md` | **When** — five lots, each with a falsifiable exit criterion and a record of what bounds it (human decisions, machine-time executions, token ceiling, repair iterations), never days |
| `docs/couverture.md` | **Where we are** — the count, the thresholds fixed after a first measurement, the per-target measures |

## Two rules that override convenience

1. **Requirements are never weakened to obtain a pass.** A threshold tuned after the fact
   measures nothing. The cahier invents no threshold at all: one appears only where the
   brief gives it, or after a first measurement recorded in `docs/couverture.md`, and is
   never lowered afterwards. `docs/plan.md` §7 records two of our own criteria as failing
   rather than declaring them out of scope.
2. **No field may be neutralised in a comparison unless an A/A run has shown it varies.**
   Identifiers are bound, never masked. `docs/architecture.md` D3 says which decides what.

## The shape of the thing

Seven packages, one per family of requirements; every step is
`python -m package.step --in DIR --out DIR` and no step imports another. Blocks that
**propose** may call a model; blocks that **pronounce** may not — no LLM client import
under `judge/`, grep-checked by the spec. Everything target-specific lives under
`targets/<target>/`.

The chain is built from maintained tools read at the source — Playwright for recording and
replay, mitmproxy2swagger and genson for inference, a fixed FastAPI + SQLAlchemy +
PostgreSQL + React stack for generated clones, Compose and PostgreSQL template databases
for environments, DeepDiff and Schemathesis for judging, FastMCP for the tool-use surface,
MLflow for model-call tracing. What remains home-made is listed in
`docs/architecture.md` §6 with the substitute that was looked for.

## The executable specification

`tests/spec/` holds the current lot's requirements as tests. They observe files a step
writes, never functions; they run on hand-written fixtures, or against a live target or
environment named by environment variables, and they **fail, never skip**, when those are
absent. They are frozen by hash (`tests/spec/MANIFEST`) and a pre-commit hook refuses a
commit that touches both the spec and a package. `tests/spec/README.md` says when
correcting the spec is legitimate.

## Where the requirements come from

A reference brief for a replication engineering role, quoted verbatim in
`docs/cahier-des-charges.md` §2 and deliberately not named. Anything that does not trace
back to it does not enter. The previous version of these documents — 91 requirements, six
thresholds the brief never gave — is tagged `docs-v0` in the history, and the cahier's §15
says what was removed and why.

## Conventions

French in `docs/` and in the spec, English in `README.md`, `CLAUDE.md`, code, commits and
branch names. Commits are `<type>(<scope>): <description>`. Not a commercial deliverable:
copyleft dependencies are not ruled out; the licence replikit itself carries is still to be
chosen.
