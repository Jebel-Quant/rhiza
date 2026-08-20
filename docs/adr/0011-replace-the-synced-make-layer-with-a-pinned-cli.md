# 11. Replace the Synced Make Layer with a Pinned CLI

Date: 2026-08-19

## Status

Accepted. Supersedes [ADR 0004](0004-adopt-modular-makefile-architecture.md).

## Context

ADR 0004 split a monolithic `Makefile` into `.rhiza/rhiza.mk` plus one fragment per feature
under `.rhiza/make.d/`, each owned by a bundle and synced only when that bundle was adopted.
The split solved what it set out to solve: a feature could be added without editing a shared
file, and a project no longer received targets for capabilities it had not asked for.

What it could not solve is that **make cannot `include` a remote file**. Every consumer
therefore held a full copy of 1481 lines at whatever template tag it last synced, and
everything downstream of that was damage control:

- **Version pinning was a copy, not a dependency.** "You are on v1.3.3" meant "these files
  were copied at v1.3.3 and nobody has edited them since", which nothing verified.
- **Local changes fought the sync.** A project that needed different behaviour shadowed the
  target in its root `Makefile` and relied on make printing `overriding commands for target`
  as evidence the mechanism worked, or added an `exclude:` entry to `template.yml` because a
  deletion alone is undone by the next sync.
- **Bugs shipped by copy and were fixed by copy.** A silently-measuring-nothing gate (#1505,
  #1511, #1516, #1534) had to be found, fixed, released and re-synced into every consumer,
  and a consumer that had shadowed the target got the fix and kept the bug.
- **Portability was ours to maintain.** `rhiza.mk` carried a forty-line probe for make falling
  back to `cmd.exe` on Windows, because its recipes were POSIX shell.
- **The recipes were untestable.** A `make -n` assertion proves the text of a command, never
  that its flags are right. go-core's licence gate needed `--ignore $(go list -m)` and no dry
  run could have found that.

The bundle model itself was never the problem — it is how a project says which capabilities it
wants, and ADR 0006 and ADR 0010 still stand. The problem is the delivery mechanism for
*executable* content, which is the same problem pytest-rhiza solved for `.rhiza/tests/`.

## Decision

Distribute the task layer as a **pinned Python package**,
[rhiza-task](https://github.com/Jebel-Quant/rhiza-task), provisioned per invocation by `uvx`.

The front door stays a `Makefile` and `core` ships it. It pins `RHIZA_TASK`, bootstraps `uv`
when the runner has none, and forwards every unmatched target to the CLI through a `%:`
catch-all. `make test` still works, because `test` is a task — not because anything in the
file mentions it.

> **Amendment (2026-08-20).** As first accepted, the CLI *printed* that file
> (`uvx rhiza-task shim > Makefile`) and each repository owned the copy from then on. That is
> reversed: the file is one of `core`'s templates, and rhiza-task defines no Makefile at all.
>
> Two things were wrong with the generated form. It put a **template inside the task runner** —
> the CLI had to know about `local.mk`, the `##` help convention and the `./bin/uvx` bootstrap,
> and rhiza then hand-carried a variant of the output anyway, so the generator was not even the
> single source it was supposed to be. And it put the **pin inside a file no sync touches**:
> `shim` wrote the version of whichever CLI printed it, so moving a consumer's gates forward was
> a per-repo hand edit `/rhiza:update` could not make. "One version bump" under *Easier* below
> was true only for someone who knew to make it.
>
> Template ownership restores the property `RHIZA_CHECKS_VERSION` has: a repo synced at a tag
> runs that tag's gates. It costs the ability to append to the `Makefile`, which two earlier
> changes had already made unnecessary — the mother-repo targets moved to `local.mk`, and
> `bundles/core/.gitignore` stopped ignoring that file (#1574) so a consumer can commit its own.

`.rhiza/rhiza.mk` and `.rhiza/make.d/` are deleted. The retirement ran in two steps:
rhiza-task 0.2.0 took eleven fragments, and 0.3.0 took the last five — `github`, `docker`,
`lfs`, `paper` and `presentation` — whose targets are conveniences rather than gates and so
had no CLI equivalent until then.

Three properties of the replacement are load-bearing:

- **The target names are unchanged.** Every task is named after the make target it replaced,
  so a consumer's muscle memory, its CI workflows and a reusable workflow pinned to an older
  rhiza all keep working.
- **`RHIZA_TASK` is the whole version contract.** Bumping one line is the migration that used
  to be re-syncing sixteen files and reconciling whatever had been shadowed.
- **Bundles still decide capability, and now decide it by configuration rather than by
  recipe.** The `docker` bundle ships the `Dockerfile`, `paper` ships the `docs/paper/`
  convention; the tasks come from the CLI in every project, and skip when the thing they act
  on is absent.

## Consequences

### Easier

- **Upgrading.** One version bump, resolved and verified by a package manager, instead of a
  file sync whose outcome depends on what the consumer had edited.
- **Fixing a bug for everyone.** A release reaches every consumer at their next bump, and a
  project that customised something did so by shadowing a *target*, which the fix does not
  touch.
- **Testing.** Task bodies are Python with a unit suite, and rhiza's own `tests/e2e/` runs the
  assembled gates against real toolchains — which catches wrong flags, as a dry run never did.
- **Portability.** Commands are argument vectors, not shell strings. There is no shell to
  detect and no `cmd.exe` fallback to probe for.
- **Configuration.** Settings resolve through a documented five-layer order ending in a
  `[tool.rhiza-task]` table, replacing `?=` defaults, `+=` accumulators and include-order
  precedence.

### Harder

- **A network and uv are required.** `uvx` provisions the CLI per invocation. The shim
  bootstraps uv itself so `make <anything>` still works on a bare runner, but an offline
  machine with a cold cache cannot run a gate.
- **Reading a recipe.** `make -n test` used to show the command. Now it shows a delegation,
  and the answer is in another repository.
- **Extending a task.** The `pre-install::`/`post-install::` hooks are gone; a project shadows
  the target with an explicit rule instead. That is more capable and less discoverable — and it
  belongs in `local.mk`, since the amendment above made the `Makefile` synced: anything appended
  to it is lost at the next `/rhiza:update`.
- **A stale fragment can shadow a task.** A sync ceasing to deliver a file does not delete it,
  so a consumer that keeps `.rhiza/make.d/` *and* an `-include` for it runs the old recipe in
  preference to the new task. Migrating repos delete the folder.
- **Two repositories to release.** A change to a gate is a rhiza-task release plus a pin bump
  here. `tests/api/test_bundle_cli_targets.py` guards the seam by asking the pinned version
  whether it still has every target the retired fragments provided.
