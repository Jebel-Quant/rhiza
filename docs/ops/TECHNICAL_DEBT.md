# Technical Debt

Known limitations and deferred work in the Rhiza **template repository**.

## Where the authoritative list lives

The [GitHub issue tracker](https://github.com/Jebel-Quant/rhiza/issues) labelled
`technical-debt`, not this file.

This document used to carry a parallel register of eleven items, and it decayed in
every way such a register decays: nine of them were marked `Related Issues: TBD` and so
were tracked nowhere, two pointed at files (`docs/DEPENDENCIES.md`, `ROADMAP.md`) that
do not exist in this repository, two described a *different* repository's problems, and
two described problems the quality gates had since fixed — while the page went on
rendering perfectly. It claimed a monthly review cadence it had not met in months.

The lesson is the reason this section is now first: a hand-maintained list that
duplicates the issue tracker will drift out of sync with the repository, and nothing in
CI can tell. `interrogate` asks whether a docstring exists; `markdownlint` asks whether
markdown is well-formed; lychee resolves `[text](target)` links but not prose paths.
None of them asks whether a *claim* is still true.

So: **file an issue.** Use this page only for context that has nowhere else to live.

## Scope — what belongs here, and what does not

Rhiza is a collection of configuration templates. The tool that *syncs* them into
downstream projects is [`rhiza-cli`](https://github.com/Jebel-Quant/rhiza-cli), a
separate repository ([ADR 0005](../adr/0005-separate-rhiza-template-from-cli.md)).

Debt in sync behaviour — conflict resolution when a template update collides with local
changes, sync performance on large repositories, pre-sync validation of a custom
template — belongs to `rhiza-cli` and should be filed there. The previous version of
this document tracked three such items against this repository, where no code
implementing them exists.

## Current items

None recorded here. Open items live in the issue tracker; see the first section.

Two standing trade-offs are worth knowing about, and neither is debt to be paid down —
each is a deliberate position, recorded so it is not rediscovered as a surprise:

- **Python 3.11 is still supported.** `pyproject.toml` sets
  `requires-python = ">=3.11"`, which keeps the CI matrix wider and rules out
  newer-only syntax. Revisit when the supported-version policy changes.
- **The e2e suite is opt-in.** `make e2e` needs real Rust and Go toolchains, so it is
  gated behind `RHIZA_E2E=1` and runs per-layer in `.github/workflows/rhiza_e2e.yml`.
  A green local `make test` therefore does not exercise the Rust or Go layers. This is
  a cost decision, documented in `CLAUDE.md` under **Language layers**.

## Previously listed, now resolved

Kept because "we already fixed that" is the most useful thing a stale list can tell its
next reader. Each names the evidence, so the claim is checkable rather than asserted.

| Item | Status | Evidence |
| --- | --- | --- |
| Documentation coverage incomplete | Resolved | `make docs-coverage` enforces 100% (interrogate); currently 100.0% over 1118 items |
| Not all Makefile targets have help text | Resolved | The "Check Makefile targets" pre-commit hook enforces `##` help text; `make help` renders it |
| No schema validation for templates | Resolved | The "Validate template-bundles.yml" and `check-jsonschema` hooks, plus `tests/bundles/test_template_bundles_schema.py` |
| Dependencies lack upper bounds | Not applicable | Rhiza declares no runtime dependencies; `uv.lock` pins the dev toolchain and Renovate updates it |
| UV package manager migration | Resolved in v0.7.0 | Unified dependency management via `uv` |
| Pre-commit hook standardization | Resolved in v0.6.5 | Standardized hooks across templates |
| GitHub Actions modernization | Resolved in v0.6.0 | Actions updated to current stable versions |

Two earlier entries were dropped rather than resolved. "Some error messages lack
actionable guidance" named no message and no file, so it could never be closed on
evidence. "No support for non-English documentation" recorded no demand signal, and
speculative work is a roadmap question, not debt.

## Recording new debt

1. Open a GitHub issue describing the limitation and its impact.
2. Label it `technical-debt`.
3. If it concerns syncing rather than the templates themselves, file it against
   `rhiza-cli` instead.
4. Add a note here **only** if the item needs context that does not fit an issue — and
   link the issue, so the two cannot drift apart.
