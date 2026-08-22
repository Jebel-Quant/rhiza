# Extending Rhiza

Two different jobs share this page:

- **Extending a rhiza-managed project** — adding your own targets, settings and steps to a
  repository that syncs from a template, in ways that survive the next `/rhiza:update`.
- **Extending Rhiza itself** — adding a bundle to this repository so every consumer can
  select it.

The first is what most readers want. Both rest on the same rule: **template-owned files are
overwritten by the next sync**, so an extension has to live somewhere the sync does not
write.

## Table of Contents

- [Where extensions live](#where-extensions-live)
- [Extending a managed project](#extending-a-managed-project)
  - [Add a target](#add-a-target)
  - [Extend a template task](#extend-a-template-task)
  - [Change a setting](#change-a-setting)
  - [What not to do](#what-not-to-do)
- [Adding a bundle to Rhiza](#adding-a-bundle-to-rhiza)
- [Troubleshooting](#troubleshooting)
- [See Also](#see-also)

---

## Where extensions live

| Location | Purpose | Committed? |
|----------|---------|------------|
| `local.mk` | Your own make targets, and shadowing a template task | ✅ Yes — it is deliberately not gitignored |
| `[tool.rhiza-task]` in `pyproject.toml` | Project settings, typed by TOML | ✅ Yes |
| `rhiza.toml` | The same settings for a project with no Python manifest | ✅ Yes |
| `pyproject.toml` (elsewhere) | Dependencies, scripts, other tools' config | ✅ Yes |
| `.rhiza/.env` | Developer-local setting overrides | ❌ No — gitignored |

**The `Makefile` is not on that list, and that is the change to absorb.** It used to be
repo-owned above an `include` line, which is where a decade of advice told you to put hooks and
variables. It is now shipped by the `core` bundle like every other config file: it pins
`RHIZA_TASK`, forwards unmatched targets to that CLI, and is overwritten wholesale by the next
sync. Anything appended to it is lost, silently — the edit works, reviews fine, merges, and
disappears at a sync weeks later.

Two things make that safe rather than merely strict. `local.mk` exists and is committable, so
repo-owned targets have a real home; and `check-managed-files` (a rhiza-hooks hook every
language layer runs) fails the commit when a managed file differs from `HEAD`, so the mistake
surfaces at commit time instead of at sync time.

Never edit anything under `.rhiza/` either. The one exception is `.rhiza/.env`, which the
template does not ship at all — it is yours to create, and gitignored, so it is for values that
should not travel with the repository.

---

## Extending a managed project

### Add a target

Put it in `local.mk`. The `Makefile` `-include`s that file, and no sync touches it:

```makefile
# local.mk
train-model: ## Train the model
	@uv run python scripts/train.py

smoke: test ## Run the suite, then hit the deployed endpoint
	@./scripts/smoke.sh
```

Two properties worth knowing:

- **A `##` comment puts the target in `make help`**, listed under *Repo-owned targets* —
  `rhiza-task list` cannot know about them, so the `Makefile`'s `help` rule greps them out of
  `MAKEFILE_LIST` and appends them.
- **Template tasks work as prerequisites.** `smoke: test` above resolves `test` through the
  catch-all, so ordering your work after a template task needs nothing special.

### Extend a template task

The `pre-install::` / `post-install::` hooks are **gone**. They were anchors declared by the
synced make layer, and the CLI that replaced it knows nothing about make targets. Nothing
warns you about this: a `post-install::` rule in `local.mk` today is a target nobody invokes.

Shadow the task instead. An explicit rule beats the `%:` catch-all, so the rule runs and can
call the task itself wherever you want it in the sequence:

```makefile
# local.mk

# The old `pre-install::` — extra work first, then the real task.
install: $(UVX)
	@command -v dot >/dev/null 2>&1 || sudo apt-get install -y graphviz
	@$(UVX) $(RHIZA_TASK) install

# The old `post-install::` — the real task first, then the extra work.
test: $(UVX)
	@$(UVX) $(RHIZA_TASK) test
	@./scripts/publish-test-report.sh
```

`UVX`, `UV` and `RHIZA_TASK` are all defined by the `Makefile` above the `-include`, so a
shadowing rule always drives the same pinned CLI as everything else. Naming `$(UVX)` as a
prerequisite keeps the bootstrap that installs `uv` on a runner that has none.

This is strictly more capable than the hooks were: it works for **every** task rather than the
six that happened to have anchors, and the order is written down rather than implied.

### Change a setting

Settings belong to the task runner, which resolves each one through a chain — later wins:

1. `rhiza-task`'s own defaults
2. `.rhiza/.env` (developer-local, `UPPER_SNAKE_CASE` keys)
3. `rhiza.toml`
4. `pyproject.toml`'s `[tool.rhiza-task]` table
5. `RHIZA_*` environment variables
6. CLI flags

The documented home for a committed setting is the table:

```toml
[tool.rhiza-task]
source-folder = "mypackage"
typechecker = "mypy"
coverage-fail-under = 80
ci-os-matrix = ["ubuntu-latest", "macos-latest"]
```

A project with no Python manifest — a crate, a Go module — uses `rhiza.toml`, which takes the
same keys either inside a `[tool.rhiza-task]` table or flat at the top level. Where both files
exist, `pyproject.toml` wins.

For a one-off, an environment variable outranks both files:

```bash
RHIZA_COVERAGE_FAIL_UNDER=80 make test
```

**Check rather than assume.** `uvx rhiza-task print coverage-fail-under` prints what a setting
currently resolves to, which is the fastest way to find out that an override is not being read
at all. That failure mode is worth taking seriously: a gate pointed at a folder that does not
exist *skips* rather than fails, so a misresolved `source-folder` makes `typecheck`, `security`
and `docs-coverage` all report success having measured nothing.

### What not to do

| Don't | Because | Do instead |
|-------|---------|------------|
| Append to the `Makefile` | Template-owned; the next sync overwrites it | `local.mk` |
| Edit anything in `.rhiza/` (except `.env`) | Same | Upstream PR, or `exclude:` in `.rhiza/template.yml` |
| Write `post-install::` anywhere | The anchors are gone; nothing invokes it | Shadow the task |
| Set `SOURCE_FOLDER` or similar in a makefile | The CLI reads settings, not make variables | `[tool.rhiza-task]` |
| Commit a fix to a template-owned workflow | It vanishes at the next sync | Upstream PR, or `exclude:` |

If a template-owned file genuinely needs to differ in your repository, `exclude:` in
`.rhiza/template.yml` stops the sync delivering it — you then own that file, and stop getting
its improvements. Prefer an upstream PR where the change makes sense for everyone.

---

## Adding a bundle to Rhiza

This half is for work in **this** repository. A bundle is a named group of files plus an entry
in `.rhiza/template-bundles.yml`; the filesystem expresses ownership, so `bundles/<name>/`
holds exactly what a consumer selecting `<name>` receives, at the paths they receive it.

### Worked example: `linter`

1. **Create the bundle directory**

   ```text
   bundles/
   └── linter/
       └── .ruff.toml
   ```

2. **Add the bundle files.** Files under `bundles/linter/` land in the downstream project at
   the same relative path. A Ruff override extending the layer's own config:

   ```toml
   # bundles/linter/.ruff.toml
   extend = "ruff.toml"

   [lint]
   extend-select = ["B", "I"]
   ```

3. **Declare it in `.rhiza/template-bundles.yml`**, with any dependencies. This one extends
   `python-core`'s `ruff.toml`, so it requires that layer:

   ```yaml
   linter:
     description: "Optional Ruff overrides for stricter linting"
     standalone: false
     requires: [python-core]
   ```

4. **Add a sync test in `tests/bundles/`** so the bundle is exercised the way a consumer
   receives it. Extending `test_bundle_combinations.py` is usually enough:

   ```python
   class TestLinterBundleSync:
       """Syncing python-core + linter adds the Ruff override file."""

       @pytest.fixture(autouse=True)
       def synced(self, tmp_path: Path, root: Path) -> None:
           sync_bundles(root, ["core", "python-core", "linter"], tmp_path)
           self.project = tmp_path

       def test_ruff_override_exists(self) -> None:
           assert (self.project / ".ruff.toml").is_file()

       def test_ruff_override_extends_the_layer_config(self) -> None:
           content = (self.project / ".ruff.toml").read_text(encoding="utf-8")
           assert 'extend = "ruff.toml"' in content
   ```

   `test_bundle_content_validity.py` picks up any new YAML or JSON automatically.

5. **Document it** in CLAUDE.md's bundle overview, README.md's bundle tables, and
   `docs/reference/BUNDLE_TAXONOMY.md`. All three are gated — see the checklist.

6. **Run the suite.** `make test` covers the bundle and documentation gates; `make rhiza-test`
   runs the conformance checks. If the bundle belongs to a language layer, `make e2e` is what
   actually executes its gates against a real toolchain.

7. **Open one PR** with the directory, the YAML entry, the tests and the documentation
   together, so a reviewer can see the whole bundle.

### Review checklist

Each item names the gate that enforces it, so a miss shows up locally rather than as a
surprise in CI:

- Bundle metadata with a `description`, and `requires` referencing existing bundles
  (gate: `tests/bundles/test_template_bundles.py::TestTemplateBundles`)
- `bundles/<name>/` exists, is non-empty, and claims no file another bundle owns — except
  within a language layer, where overlap is the design
  (gate: `tests/bundles/test_template_bundles.py::TestTemplateBundles`)
- The bundle is named in CLAUDE.md
  (gate: `tests/docs/test_doc_consistency.py::TestBundleDocumentation`)
- The bundle is listed in README.md's bundle tables
  (gate: `tests/docs/test_doc_consistency.py::TestReadmeBundleList` — which also fails on a
  table row for a bundle that does *not* exist)
- The bundle appears in `docs/reference/BUNDLE_TAXONOMY.md`
  (gate: `tests/docs/test_doc_consistency.py::TestBundleTaxonomyDoc`)
- Platform compatibility is picked up automatically from the YAML
  (gate: `tests/bundles/test_bundle_matrix.py` — nothing to write, but a failure for
  `<name>` points at a YAML, ownership or dependency problem)
- The synced output has a focused test (the one you wrote in step 4)

---

## Troubleshooting

For sync failures and recovery commands, see [docs/troubleshooting.md](../troubleshooting.md).

### A target does not appear in `make help`

`make help` lists the CLI's tasks and then greps `MAKEFILE_LIST` for repo-owned rules carrying
a `##` comment. No comment, no listing — and a target defined anywhere other than `local.mk`
(or a file it includes) is not in `MAKEFILE_LIST` at all.

### A `post-install::` rule never runs

It never will: the anchors retired with the synced make layer. See
[Extend a template task](#extend-a-template-task).

### A shadowing rule is ignored

An explicit rule beats the pattern rule, so this is almost always a name mismatch — check
`uvx rhiza-task list` for the exact task name. Note also that the shadow *replaces* the task:
if the rule does not call `$(UVX) $(RHIZA_TASK) <task>`, the template's work simply does not
happen.

### A setting has no effect

Run `uvx rhiza-task print <setting>` to see what resolves. The usual causes are a key in the
wrong case (`.rhiza/.env` takes `UPPER_SNAKE_CASE`, the TOML tables take `kebab-case`), a
`[tool.rhiza-task]` table shadowing the `rhiza.toml` you were editing, or an assignment in a
`Makefile`, which the CLI does not read.

### A gate passes but measures nothing

Almost always a path setting pointing somewhere that does not exist — the gates skip a missing
folder rather than failing. `uvx rhiza-task print source_folder` and confirm the folder holds
the code you expect.

### An edit to a workflow keeps disappearing

The file is template-owned. `check-managed-files` should have refused the commit; if it did not
run, the sync silently reverted the edit. Send the change upstream, or `exclude:` the file and
own it.

---

## See Also

- [Customization Guide](CUSTOMIZATION.md) — the same extension points with more worked
  examples, plus CodeQL and documentation configuration
- [Quick Reference](QUICK_REFERENCE.md) — command and file cheat sheet
- [Tools Reference](../reference/TOOLS_REFERENCE.md) — what each tool in the stack does
- [Bundle Taxonomy](../reference/BUNDLE_TAXONOMY.md) — every bundle and profile
- [Makefile Customisation](../../README.md#makefile-customisation) — the shim, the pin, and
  where settings live
- [rhiza-education Lesson 10: Customising Safely](https://github.com/Jebel-Quant/rhiza-education/blob/main/lessons/10-customizing-safely.md)
  — tutorial walkthrough of these mechanisms
