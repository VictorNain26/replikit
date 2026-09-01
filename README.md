# replikit

A software replication platform: take a third-party application observable only from the
outside, produce a locally runnable clone, and **prove** the clone is behaviourally
indistinguishable from it on a declared scope.

The hard part is not the clone. It is the oracle — deciding, reproducibly and
automatically, that two systems behave identically for the same sequence of inputs. The
published state of the art does not solve it. It does not claim to: VeriEnv (arXiv
2603.10505) clones real websites into environments with "deterministic, programmatically
verifiable rewards", and those rewards verify that a *task* was completed, never that the
environment resembles the original. REAL claims high-fidelity replicas and describes no
validation protocol at all. That gap is what this repository is about.

## Status

**Documentation only.** No product code yet. `docs/couverture.md` holds the count, and it is
the only place that number lives. That is the honest state of a project that is starting.

The one script here, `tools/check_plan_coverage.py`, exists because the plan asserts that
every blocking requirement and every architectural block is assigned to a lot. Without the
script that assertion would be unverifiable — which the rules below forbid. It checks every
count and mapping the documents claim, and ships with a self-test that mutates them to
confirm the check still bites.

```bash
python tools/check_plan_coverage.py              # every requirement and block carried, exit 0
python tools/check_plan_coverage.py --self-test  # drops an assignment, expects exit 1
```

## The four documents

Read them in this order. Each answers one question, owns one namespace of identifiers, and
repeats none of the others.

| Document | Question |
|---|---|
| `docs/cahier-des-charges.md` | **What** — 91 requirements, 64 blocking, and the eleven acceptance criteria a clone must meet |
| `docs/architecture.md` | **How** — assumed limits, eight decisions, seven packages, one tool or paper per requirement, each reference carrying its verification status |
| `docs/plan.md` | **When** — six lots, each with a falsifiable exit criterion |
| `docs/couverture.md` | **Where we are** — the count, and the only place it lives |

## Two rules that override convenience

These are why the project exists. Everything else is negotiable.

1. **Requirements and thresholds are never weakened to obtain a pass.** A threshold tuned
   after the fact measures nothing. Two forms are refused by name: loosening a comparison
   because a diff is noisy, and shrinking the declared scope so "zero gaps" becomes true by
   construction. **A red check that is honest is worth more than a green one that was
   negotiated** — including when it is ours: `docs/plan.md` §7 records one of our own
   acceptance criteria as failing rather than declaring it out of scope.
2. **No field may be neutralised in a comparison unless an A/A run has shown it varies.**
   `docs/architecture.md` D2 records the shape the violation takes, and the counter-example
   that motivated the rule.

## The shape of the thing

Seven packages, one per section of the requirements. A block is a function
`artefacts -> artefacts`; no block calls another.

```
observe/       target         -> traces            (CAP)
infer/         traces         -> specification     (INF)
build/         specification  -> clone             (GEN)
run/           clone          -> environments      (RUN, NF)
serve/         clone          -> agent surface     (API)
judge/         target x clone -> gaps              (VER, ACC)   -- no LLM here
orchestrate/   the loop                            (LLM)
targets/<t>/   the only target-specific place
```

The frontier that matters: blocks that **propose** may call a model, blocks that
**pronounce** may not. Grep-checkable — no LLM client import under `judge/`.

## How it is sequenced, and why

The clone is written by an agent from the first lot, and judged by code. That ordering is
argued, not assumed: self-repair loops gain little when a model reviews its own output and
substantially more when the feedback is stronger (Olausson et al., ICLR 2024), so the loop is
worth closing as soon as a deterministic critic exists. The corollary is the constraint that
comes with it — once a gap list is an agent's feedback it is also its reward function, and a
fixed reward gets optimised rather than satisfied (*The Verification Horizon*, arXiv
2606.26300). Hence requirement `VER-11`: every gap count is published with the oracle's
detection rate, and the seeded fault set is never shown to the generator.

The second target lands in lot 3, before the runtime, because a runtime built for one target
is a runtime for one target. `docs/plan.md` §2 carries the full argument.

## Where the requirements come from

They are traced, one family at a time, to a reference brief for a replication engineering
role, which `docs/cahier-des-charges.md` §13 deliberately does not name. Anything that does
not trace back is marked as an extension and does not gate delivery — with one documented
exception, `VER-11`, which is admitted to the core because `ACC-01` is meaningless without it.

**No code is carried over from anywhere.** `docs/plan.md` §6 gives the three architectural
constraints that rule out reusing existing work: the Playwright versions two blocking
requirements need, decision D6 on privileged access, and the fact that a harness judging
*tasks against an environment* does not convert into one judging *an environment against its
target*.

That last distinction is the whole product. VeriEnv buys plausible diversity — many
environments, agents that generalise. replikit buys fidelity to one target.

## Conventions

French in `docs/`, English in `README.md`, `CLAUDE.md`, code, commits and branch names.
Commits are `<type>(<scope>): <description>`.

This is not a commercial deliverable, so copyleft dependencies are not ruled out. The licence
replikit itself carries is still to be chosen.
