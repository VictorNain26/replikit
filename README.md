# replikit

**What it does.** replikit takes a web application you do not own — reachable only through
a browser and its API, or through its source code when it is open — and produces a clone
you can run locally: same screens, same API, same rules, same error messages, resettable to
a named state in one command. Then it proves the clone is faithful: it replays the same
recorded journeys on the original and on the clone and reports every difference, with the
trace that reproduces it.

**Why.** Training AI agents needs interactive, resettable environments that behave like
real software. Building them by hand is slow, and building them with AI agents produces
plausible code that is wrong in ways nobody notices — unless something checks. The
published systems that clone real websites verify that an agent *completed a task*; none of
them verifies that the environment *resembles the original*. replikit is that missing check,
built as the toolchain a *Replication Engineer* would use every day. It is a demonstrator:
the goal is to show, on two real targets, that the method works and to publish the numbers.

**How, in one paragraph.** Record journeys on the target with Playwright (network, DOM,
accessibility tree, WebSocket frames). Infer the API and the data model from the recording
with maintained tools (mitmproxy2swagger, genson). Let a coding agent write the clone on a
fixed stack (FastAPI, SQLAlchemy, PostgreSQL, React), inside a workspace that cannot see the
test faults. Run the clone under Docker Compose with a PostgreSQL template database for
resets. Replay the same journeys on the clone, compare the two traces with DeepDiff under a
noise policy justified by replaying the target against itself, and publish three numbers
together or not at all: the list of gaps, the detection rate of the comparator on seeded
faults, and the number of repair iterations the agent needed. Expose the clone to agents
through HTTP and MCP so both interaction modes — a browser, or tool calls — run on the same
state.

## Status

**Documentation and an executable specification. No product code yet.**
`docs/couverture.md` holds the count and it is the only place that number lives.

```bash
make check   # the four documents agree, the checker's self-test bites, the spec is frozen
make spec    # the executable specification, all lots -- red until the steps exist
make lot1    # lot 1's spec, then its three numbers; exits non-zero until they exist
```

## Read this, in this order

| Document | Question it answers |
|---|---|
| `docs/cahier-des-charges.md` | **What** must the toolchain do? Every requirement quotes the sentence of the reference brief it comes from, says what it measures, and names the standard its output follows. No threshold is invented. |
| `docs/architecture.md` | **How** is each requirement carried? One verified tool per requirement, the decisions that shape the chain and what each costs, what remains home-made and the substitute that was looked for, what is unresolved, what was discarded and why. |
| `docs/plan.md` | **When**, in what order, and what bounds each lot — human decisions, machine-time runs, token ceiling, repair iterations. Never days: agents write the code. |
| `docs/couverture.md` | **Where we are**: the count, the thresholds fixed after a first measurement, the per-target numbers. |
| `tests/spec/README.md` | How the executable specification works and when it may be corrected. |

## What makes the method honest

- **The comparator is tested before it judges.** Faults are seeded into recorded traces;
  the comparator must catch them, and its detection rate is published next to every gap
  count. A count of zero gaps without that rate is not a result.
- **Nothing is neutralised without evidence.** A field is ignored in a comparison only if
  replaying the target against itself showed it varies. Identifiers are bound to variables
  and checked for consistency, never masked.
- **A model proposes, code decides.** The agent writes the clone; a deterministic comparator
  judges it. No model client is imported under `judge/`, and the spec greps for it.
- **The spec is frozen.** Requirements live as tests that observe files a step writes,
  never functions. They are hashed, a pre-commit hook refuses a commit that touches both
  the spec and code, and a correction must show the test was wrong — not that the code
  could not pass.
- **Thresholds come from measurements.** The brief gives one number ("hours rather than
  weeks"); the cahier adds none. Each requirement says what it measures; a threshold is
  born in `docs/couverture.md` from a first value and is never lowered.
- **What cannot be held is recorded as failing**, not dropped: the review a Curriculum
  Engineer must give, the migration of an environment this repository does not have.

## Layout

```
docs/          the four documents
tests/spec/    the executable specification, one directory per lot, hand-written fixtures
tools/         the checker that recounts the documents, and the spec freeze
observe/ infer/ build/ run/ serve/ judge/ orchestrate/   the seven packages of steps (empty)
commun/        code shared by steps
targets/<t>/   everything specific to one target: scenarios, scope, policy, compose, clone
judge/faults/  the seeded faults, kept out of the clone-writing agent's workspace
```

Every step is `python -m package.step --in DIR --out DIR`; `make` composes them; no step
imports another. Python for the chain, TypeScript and React for the generated front-end.

## Where the requirements come from

A reference brief for a replication engineering role, quoted verbatim in
`docs/cahier-des-charges.md` §2 and deliberately not named. Anything that does not trace
back to it does not enter. The previous version of these documents is tagged `docs-v0` in
the history; the cahier's §15 says what was removed and why.

## Conventions

French in `docs/` and `tests/spec/`, English in `README.md`, `CLAUDE.md`, code, commits and
branch names. Commits are `<type>(<scope>): <description>`. Not a commercial deliverable:
copyleft dependencies are not ruled out; the licence replikit itself carries is still to be
chosen.
