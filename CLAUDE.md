# CLAUDE.md

How to work in this repository. **Practices only.** Every technical decision lives in
`docs/`, and this file may cite one but never restates it — if you find a design decision
written here, it is a bug in this file.

## The four documents, and the rule that keeps them apart

| Document | Question | Owns the namespace |
|---|---|---|
| `docs/cahier-des-charges.md` | **what** | `XXX-NN`, and the brief's anchors `O1`–`O9`, `M1`, `M2`, `S1`, `S2`, `R` |
| `docs/architecture.md` | **how** | `Pn`, `Dn`, step names `package/step` |
| `docs/plan.md` | **when** | `lot n` |
| `docs/couverture.md` | **where we are** | the statuses, the count, the thresholds fixed after a first measurement |

**A document may cite another's identifier. It may never define one.** A paragraph that
explains what `D3` *means* belongs to `architecture.md`, wherever you found it. Section
numbers are anchors — never renumber one. Read all four before designing anything. French
in `docs/` and `tests/spec/`, English everywhere else.

```bash
make check     # document coherence, the checker's own self-test, and the spec freeze
make spec      # the executable specification -- red until the steps exist
make lot1      # a lot's exit criterion; exits non-zero until the lot is actually held
```

Run `make check` after changing the shape of any table the checker reads: the cahier's
requirement rows, architecture §4 and §5, plan §6, couverture §1.

## Rules that override convenience

**1. Requirements are never weakened to obtain a pass.** No threshold is invented: the
cahier states what each requirement measures, and a threshold is born in
`docs/couverture.md` §2 from a first measurement, then never lowered. Do not narrow the
declared scope or pick an easier probe. When a verification cannot be run as specified, say
so and leave it failing — `docs/plan.md` §7 does exactly that for two of our own criteria.

**2. No field may be neutralised in a comparison unless an A/A record shows it varies.**
Identifiers are bound (D3), never masked. This applies to every comparison you write, not
only the oracle.

**3. A tool before a line.** Before writing code that does not exist elsewhere, look for a
maintained tool or a standard, read it at the source, and cite the URL and the passage. If
none fits, the substitute you looked for and why it was rejected go into
`docs/architecture.md` §6 **in the same commit as the custom code**; a discarded tool goes
to §8 with its motive. Never state a version, an API or a published figure from memory:
`docs/architecture.md` §9 carries a verification status per reference, and promoting an
entry requires quoting the passage.

## The executable specification is frozen

`tests/spec/` holds the current lot's requirements as tests. They observe the files a step
writes — every step is `python -m package.step --in DIR --out DIR`, see
`docs/architecture.md` §4 — never its functions. Three families: greps and `--help`
(always run), hand-written fixtures (always run, target off), live target or environment
(markers `cible` and `environnement`, fail without their variables, **never skip**).

**A commit may not touch both `tests/spec/` and a package.** `.githooks/pre-commit` refuses
it — enable once with `git config core.hooksPath .githooks`. `tools/check_spec_frozen.py`
compares every spec file, fixtures included, to its hash in `tests/spec/MANIFEST`.

**Correcting the spec is legitimate** when a test failed, or passed, for the wrong reason —
not when the code could not satisfy it. The commit carries a reproducible demonstration on
a stub tree, and runs `check_spec_frozen.py --update` in that same isolated commit. Before
freezing a new test, watch it fail and read the message; name its casse in the docstring.

## Where code goes

Seven packages under the repository root, `commun/` for code shared by steps,
`targets/<target>/` for everything target-specific, `judge/faults/` for the seeded faults
(`docs/architecture.md` §4). Three greps the spec runs, and you should run before
committing:

- **P1** — no module of the seven packages imports a module of the seven packages, its own
  package included. `commun/` may be imported; a step may not.
- **P3** — no LLM client import under `judge/`, and no step under `judge/` drives a model.
- **P5** — no target name under the seven packages.

The agent that writes a clone runs in a reduced workspace without `judge/` (D4); if you
are that agent, the absence is deliberate — do not look for the faults elsewhere.

## Conventions

- Commits: `<type>(<scope>): <description>` — `feat`, `fix`, `chore`, `refactor`, `test`,
  `docs`, `style`, `perf`, `ci`, `build`. A commit that changes a third-party config or
  promotes a reference to verified **cites its source in the message**.
- Stage file by file. Never `--no-verify`, never skip a hook.
- Announce and confirm before anything irreversible — force push, `reset --hard`, remote
  branch deletion, merging or closing a PR.
- Zero comments by default; a comment earns its place only for a non-obvious *why*.
- YAGNI. No abstraction, flag, or compatibility shim for a need that does not exist.
- Never say a lot is done, green, or fixed without having run its exit criterion and read
  the exit code. Lots are not estimated in days: `docs/plan.md` §3 says what bounds them.
