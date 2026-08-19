# What lives in `.rhiza/make.d/`

Almost nothing, now. This folder used to hold the whole build system — eleven fragments
defining every gate, loaded by `.rhiza/rhiza.mk`. That moved to
[rhiza-task](https://github.com/Jebel-Quant/rhiza-task), a pinned CLI, and your `Makefile` is a
generated shim that forwards to it.

What remains here are the fragments for bundles the CLI has no task for yet:

| file | bundle | targets |
| --- | --- | --- |
| `github.mk` | `github` | `view-prs`, `view-issues`, `workflow-status`, `failed-workflows`, `latest-release`, `whoami` |
| `docker.mk` | `docker` | `docker-build`, `docker-run`, `docker-clean` |
| `lfs.mk` | `lfs` | `lfs-install`, `lfs-pull`, `lfs-track`, `lfs-status` |
| `paper.mk` | `paper` | `paper`, `paper-clean` |
| `presentation.mk` | `presentation` | `presentation`, `presentation-pdf`, `presentation-serve` |

You only receive the ones whose bundle you selected. They are template-managed: edit the bundle
source upstream, not the copy here. They retire as rhiza-task grows tasks for them
([rhiza-task#20](https://github.com/Jebel-Quant/rhiza-task/issues/20)).

## Your Makefile

Generate it once and commit it. It is **yours** — nothing syncs over it:

```bash
uvx rhiza-task shim > Makefile
```

It is about a dozen lines. A `%:` catch-all forwards any target it cannot resolve to the CLI, so
`make test`, `make fmt` and `make all` work exactly as before while the file contains no recipes.
`RHIZA_TASK` at the top is the entire version contract: bumping that one line is the upgrade that
used to be a re-sync of eleven fragments plus reconciling whatever you had shadowed.

To load the fragments above, the shim needs these two lines — add them if your generated copy
lacks them:

```make
-include .rhiza/make.d/*.mk
.rhiza/make.d/%.mk: ;
```

The second is not decoration. An included makefile is also a target `make` tries to *remake*, and
with `%:` in scope that attempt is forwarded to the CLI — so without it every single invocation
opens with `unknown task: docker.mk`. The shim carries the same trick for `local.mk`.

## Recipes

### Add a task

Put it straight in your `Makefile`. An explicit rule beats the `%:` catch-all, so it wins:

```makefile
train: ## Train the model using local data
	@uv run python scripts/train.py
```

### Change a setting

Settings are no longer make variables. They live in a `[tool.rhiza-task]` table in
`pyproject.toml` (or `rhiza.toml`, which any language can use):

```toml
[tool.rhiza-task]
source-folder = "mypackage"
typechecker = "both"
coverage-fail-under = 80
```

`uvx rhiza-task print source-folder` shows what a setting resolves to, which is the fastest way to
check that an override took effect. The resolution order, lowest first: built-in defaults →
`.rhiza/.env` → `rhiza.toml` → `[tool.rhiza-task]` → `RHIZA_*` environment variables → CLI flags.

Note that `.rhiza/.env` is **gitignored**, so it is for developer-local values only — CI checks
your repository out and never sees it. Anything CI must resolve belongs in a committed file.

### Run something before or after a gate

The old `pre-install::`/`post-install::` hooks are gone: the CLI knows nothing about make targets,
so a double-colon rule in your Makefile never fires. **Shadow the target instead** — an explicit
rule beats the catch-all, so call the CLI yourself and add your step:

```makefile
install:
	@uvx $(RHIZA_TASK) install
	@./scripts/seed-dev-data.sh
```

### Keep a private shortcut

`local.mk` is gitignored and `-include`d by the shim, so anything there is yours alone:

```makefile
# local.mk
t: ; @uvx $(RHIZA_TASK) test
```

## Discovering what exists

`make help` lists the CLI's tasks. It does **not** list targets from the fragments above or from
your own Makefile, because the CLI cannot see them — a known gap, tracked in rhiza-task#20. Until
it closes, `grep '##' Makefile .rhiza/make.d/*.mk` is the honest answer.
