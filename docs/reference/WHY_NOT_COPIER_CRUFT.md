# Why Not Copier or Cruft?

A question that comes up regularly: tools like [copier](https://copier.readthedocs.io/) and
[cruft](https://cruft.github.io/cruft/) already solve "keep a generated project in sync with its
template" — why does Rhiza exist instead of building on one of them?

The short answer: copier and cruft are *template renderers with an update step*. Rhiza is a
*file synchronizer with an ownership model*. The two approaches start from different premises,
and the differences compound. This document walks through them.

## What copier and cruft do

Both tools descend from the [cookiecutter](https://cookiecutter.readthedocs.io/) lineage of
project generators:

- **cookiecutter** renders a Jinja-templated directory tree once, driven by an interactive
  questionnaire. After generation, the project has no remaining link to the template.
- **cruft** adds updating on top of cookiecutter. It stores the template reference and your
  questionnaire answers in `.cruft.json`. On `cruft update`, it re-renders the old and new
  template versions, computes the diff between them, and applies that diff to your project as a
  git patch. Hunks that no longer apply are written out as `.rej` files for manual resolution.
- **copier** is a templating engine of its own (also Jinja-based) with native update support.
  It stores answers in `.copier-answers.yml`; `copier update` replays your answers against the
  new template version and performs a three-way merge, leaving inline conflict markers where
  your edits and the template's changes collide.

Common to all three: the template is a tree of Jinja files, the generated project carries a
machine-written answers file as state, and updates work by merging template changes into files
you may have edited.

## Where Rhiza starts from different premises

### 1. Verbatim files instead of templates

Rhiza files contain no Jinja. Every file a downstream project receives is byte-for-byte the
file that lives in this repository — and this repository is itself a working project that runs
those exact files. The Makefiles, CI workflows, and linting configs you sync are the same ones
that build, test, and release Rhiza itself.

This is the single most consequential difference:

- **Templates are tested by execution, not by render-then-test.** A `ci.yml.jinja` cannot be
  fed to actionlint; a `Makefile.jinja` cannot be run. Every Jinja template needs a rendering
  harness before any tool can validate it, and template bugs (a misplaced `{% endif %}`, an
  undefined variable in a rarely-taken branch) surface only in downstream projects. Rhiza's own
  CI runs actionlint, shellcheck, yamllint-style checks, and the full test suite against the
  literal files that ship.
- **Diffs are plain diffs.** A downstream project comparing its synced files against upstream
  sees an ordinary file diff — no mental rendering step, no answers to substitute. Sync PRs are
  reviewable by anyone who can read the file format.
- **The trade-off is real:** verbatim files cannot embed per-project values like a package
  name. Rhiza avoids needing them by scoping itself to project-agnostic infrastructure (see
  next point) and by moving variability from *render time* to *run time* — Make variables,
  `pyproject.toml`, and hook targets carry the project-specific parts.

### 2. Scope: development infrastructure, not project scaffolding

Copier and cruft templates typically generate an entire project — source layout, package
directories, module names, README. That whole-project ambition is precisely what forces Jinja:
`src/{{ package_name }}/__init__.py` cannot exist without templating.

Rhiza deliberately refuses that scope. It syncs only the development infrastructure layer:
Makefiles, CI/CD workflows, linting and test configuration, container setups, documentation
tooling. Your source code, package name, and project identity are never touched. Within that
narrowed scope, almost nothing needs parameterization — which is what makes the verbatim model
viable in the first place.

### 3. Composition through bundles, not one monolithic template

A cookiecutter or copier project is generated from *one* template. Conditional features are
expressed inside that template as Jinja branches (`{% if use_docker %}`), which means every
feature combination multiplies the template's internal complexity, and adopting a new feature
after generation is awkward.

Rhiza composes instead: 23 atomic bundles, each owning a disjoint set of files, with explicit
`requires`/`recommends` relationships, plus profiles as curated presets
([ADR-0006](../adr/0006-organise-templates-into-bundles.md),
[ADR-0010](../adr/0010-layered-bundle-profile-model.md)). A project adopts `marimo` or drops
`docker` by editing one list in `.rhiza/template.yml` and re-syncing. There is no questionnaire
to replay and no template-wide render to reconcile.

### 4. Ownership instead of merging

This is the deepest philosophical split. Copier and cruft assume you will edit generated files,
and their update step exists to merge upstream changes into your edits. The failure modes
follow directly: cruft's `.rej` files and copier's conflict markers both demand manual
resolution, which means updates cannot be fully automated — a bot cannot resolve a merge
conflict.

Rhiza instead draws a hard boundary:

- **Template-managed files** (everything under `.rhiza/`, synced workflow stubs) are owned by
  the template and overwritten on every sync. You do not edit them.
- **User space** is explicit and survives every sync: hook targets (`pre-install::`,
  `post-sync::`) and custom targets in the root `Makefile`, per-developer overrides in
  `local.mk`, project configuration in `pyproject.toml`. See the
  [Customization Guide](../guides/CUSTOMIZATION.md).
- A file you genuinely must diverge on can be excluded from sync, or the change can be
  upstreamed — to this repository or to your organisation's fork.

Merge conflicts are not resolved better; they are eliminated by construction. The cost is
discipline: you cannot casually tweak a managed file and expect the tweak to persist. In
practice that constraint is the feature — it is what keeps a fleet of repositories actually
identical instead of approximately identical.

### 5. Declarative intent instead of replayed answers

Rhiza's entire downstream state is `.rhiza/template.yml`: a repository, a ref, and a list of
profiles or bundles. It is short, human-written, and expresses *intent*.

`.copier-answers.yml` and `.cruft.json` are machine-generated snapshots of a past questionnaire.
They must be preserved and replayed for updates to work; hand-editing them is error-prone, and
losing or corrupting them strands the project. The difference matters most years into a
project's life, when nobody remembers the original generation.

### 6. Updates as dependency bumps

Because the template version is a plain git ref in a YAML file, it behaves like any other
pinned dependency: Renovate bumps `ref:` in `.rhiza/template.yml`, the sync workflow applies
the new files and opens a pull request, and the project's own CI gates the result. No human
runs an update command; no merge conflict can stall the bot, because synced files are never
locally modified (point 4). Updating fifty repositories means merging fifty green PRs.

Cruft and copier updates are, by design, interactive local operations. CI wrappers for them
exist, but the moment a conflict appears the automation hands back to a human — and conflicts
are routine, because editing generated files is the expected workflow.

### 7. Fork-friendly without forking an engine

Rhiza separates the template content from the sync engine
([ADR-0005](../adr/0005-separate-rhiza-template-from-cli.md)): `rhiza-cli` is generic, and
`.rhiza/template.yml` can point at any repository. An organisation that wants its own variant
forks this repository, adjusts files, and keeps pulling upstream improvements with ordinary
`git merge` — because the files are verbatim, fork maintenance is plain git work, not Jinja
template surgery.

## When copier or cruft is the better tool

This is a set of trade-offs, not a verdict. Reach for copier or cruft when:

- **You are scaffolding whole projects.** Generating `src/<package>/` layouts, parameterized
  READMEs, or license choices requires templating. Rhiza intentionally does not do this.
- **Per-project parameterization is essential.** If many synced files must embed
  project-specific values, the verbatim model fights you.
- **Downstream edits to generated files are a requirement.** If your teams must be free to
  modify any generated file and still receive upstream changes merged into it, copier's
  three-way merge is built for exactly that — with the conflict-resolution cost that follows.
- **You want template logic.** Conditional files, loops, and questionnaire-driven variation
  are first-class in copier and absent from Rhiza by design.

The approaches also compose: a reasonable setup is to scaffold a new project once with
cookiecutter or copier, then hand its development infrastructure over to Rhiza for the rest of
its life. One-shot generation and continuous synchronization solve different halves of the
problem.

## Summary

| Aspect | copier / cruft | Rhiza |
|--------|----------------|-------|
| Template format | Jinja-templated trees | Verbatim working files |
| Template validation | Render, then test | The template repo runs its own files in CI |
| Scope | Whole project, including source | Development infrastructure only |
| Feature variation | Jinja conditionals in one template | Composable bundles and profiles |
| Downstream state | Machine-written answers file | Hand-written `template.yml` (repo, ref, bundles) |
| Local customization | Edit generated files, merge later | Dedicated extension points; managed files never edited |
| Update conflicts | `.rej` files / conflict markers, resolved by hand | Eliminated by ownership boundary |
| Automated updates | Possible until the first conflict | Renovate bump → sync PR → CI gate, end to end |
| Organisation variants | Fork and maintain Jinja templates | Fork and `git merge` plain files |
