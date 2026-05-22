## [unreleased]

### 🚀 Features

- Update CHANGELOG.md on every release via git-cliff (#1052)

### 🐛 Bug Fixes

- *(docker)* Upgrade pip to 26.1 to fix CVE-2026-6357 (#1058)
## [0.10.7] - 2026-05-17

### 🚀 Features

- *(ci)* Parameterize CI OS matrix via RHIZA_CI_OS_MATRIX (#1040)

### 💼 Other

- Bump version 0.10.6 → 0.10.7
## [0.10.6] - 2026-05-06

### 🚀 Features

- Introduce layered bundle/profile model with local-first bundles (#1028)

### 🐛 Bug Fixes

- *(tests)* Skip GitHub-specific security checks when github bundle not included (#1027)

### 💼 Other

- Bump version 0.10.5 → 0.10.6

### ⚙️ Miscellaneous Tasks

- Restore renovate.json
## [0.10.5] - 2026-04-29

### 🚀 Features

- *(ci)* Add coverage regex to ci:test job
- Add no-python-cache-files local pre-commit hook (#1026)

### 💼 Other

- Bump version 0.10.4 → 0.10.5
## [0.10.4] - 2026-04-27

### 🚀 Features

- Move semgrep.yml from .github to .rhiza (#1020)

### 🐛 Bug Fixes

- Ensure _book output dir exists before touching .nojekyll
- *(book)* Pin zensical>=0.0.36 to avoid stale CI cache resolving broken older version

### 💼 Other

- Bump version 0.10.3 → 0.10.4
## [0.10.3] - 2026-04-25

### 🚀 Features

- *(core)* Add .rhiza/utils to core bundle

### 🐛 Bug Fixes

- *(security)* Warn on tooling CVEs, fail only on runtime dep vulnerabilities (#1016)

### 💼 Other

- Bump version 0.10.2 → 0.10.3
## [0.10.2] - 2026-04-22

### 🐛 Bug Fixes

- *(ci)* Use git lfs install --force to avoid hook conflict on runners
- *(ci)* Use git lfs install --force to avoid hook conflict on runners

### 💼 Other

- Bump version 0.10.1 → 0.10.2

### ⚙️ Miscellaneous Tasks

- Replace removed workflows with current rhiza equivalents
## [0.10.1] - 2026-04-18

### 💼 Other

- Bump version 0.10.0 → 0.10.1
## [0.10.0] - 2026-04-17

### 🚀 Features

- Add .bandit INI file as single source of truth for bandit configuration (#997)

### 💼 Other

- Replace `uvx uv run` with `uv run --script` in marimo workflow (#1004)
- Bump version 0.9.5 → 0.10.0

### 🚜 Refactor

- Move `adr` target from root Makefile to `.rhiza/make.d/gh-aw.mk` (#1011)

### 📚 Documentation

- Fix template documentation issues from Copilot review (#999)

### 🧪 Testing

- Add tests for rhiza_weekly.yml jobs and Makefile targets (#994)
## [0.9.5] - 2026-04-13

### 💼 Other

- Add CI job to catch unresolved .rej patch files
- Extend conflict check to also catch merge conflict markers
- Bump version 0.9.4 → 0.9.5
## [0.9.4] - 2026-04-13

### 💼 Other

- Bump version 0.9.3 → 0.9.4
## [0.9.3] - 2026-04-13

### 🚀 Features

- *(core)* Add important docs files and folders to core bundle (#991)

### 💼 Other

- Bump version 0.9.2 → 0.9.3
## [0.9.2] - 2026-04-12

### 💼 Other

- Bump version 0.9.1 → 0.9.2
## [0.9.1] - 2026-04-12

### 🚀 Features

- *(docs.mk)* Add MKDOCS_EXTRA_PACKAGES to extend uvx package list without editing template (#975)
- *(gitlab)* Bring GitLab rhiza_validate to parity with GitHub Actions equivalent (#952)

### 🐛 Bug Fixes

- *(book)* Use MARIMO_FOLDER in _book-notebooks, fix double-nested links, narrow .gitignore (#973)

### 💼 Other

- Bump version 0.9.0 → 0.9.1
## [0.9.0] - 2026-04-03

### 💼 Other

- Bump version 0.8.21 → 0.9.0

### ⚙️ Miscellaneous Tasks

- Merge origin/main into main, keep workflow consolidation from release/v0.8.21
## [0.8.21] - 2026-04-03

### 🚀 Features

- Add suppression-audit makefile target (#896)
- Use git-cliff for release notes in rhiza_release.yml (#901)
- Add lychee link check workflow and fix make security (#906)
- Add `license` make target to quality.mk for license compliance scanning (#914)
- Add rhiza_paper.yml — LaTeX paper compilation workflow (#920)
- Exclude recipe/meta.yaml from check-yaml pre-commit hook (#931)
- Relocate Marimo notebooks to docs/notebooks (#939)
- Add .gitlab/workflows/rhiza_quality.yml as GitLab equivalent of GitHub quality workflow (#950)
- Add `license` make target to quality.mk for license compliance scanning (#914)

### 🐛 Bug Fixes

- Analyse-repo target uses Claude CLI instead of Copilot CLI (#902)
- Resolve broken file references in README and template bundles
- Update rhiza_paper.yml paths from paper/ to docs/paper/

### 💼 Other

- Bump version 0.8.16 → 0.8.17
- Bump version 0.8.20 → 0.8.21

### 🚜 Refactor

- Consolidate individual rhiza_ CI workflows into rhiza_quality and rhiza_validate (#940)

### 📚 Documentation

- Update requirements README to reflect current dependencies
- Clean up README formatting and remove outdated references

### ⚙️ Miscellaneous Tasks

- Remove branch-based trigger restrictions from rhiza_sync workflow
- Sync .github/agents from tschm/jquantstats
- Consolidate root-level community files into .github/ (#938)
- Move paper into docs/paper (#945)
- Move presentation/ folder to docs/presentations/ (#948)
- Merge main into release/v0.8.21, keep workflow consolidation
## [0.8.20] - 2026-04-02

### 🐛 Bug Fixes

- Align rhiza_weekly.yml comment with actual triggers
- Add pull_request trigger and fix on: syntax in rhiza_ci.yml

### 💼 Other

- Bump version 0.8.19 → 0.8.20

### 📚 Documentation

- Fix bibliography formatting and add bibtex to paper build

### ⚙️ Miscellaneous Tasks

- Update semgrep config path to .rhiza/semgrep.yml
- Consolidate GitHub Actions workflows
- Consolidate GitLab CI workflows to mirror GitHub Actions structure
## [0.8.19] - 2026-04-01

### 🚀 Features

- Add GitLab CI workflows for link checking and paper compilation

### 🐛 Bug Fixes

- Update broken markdown links to correct file paths

### 💼 Other

- Bump version 0.8.18 → 0.8.19

### ⚙️ Miscellaneous Tasks

- Update template-bundles.yml to replace deprecated workflows with `rhiza_quality.yml`
- Simplify CI trigger by removing branch restrictions
- Remove branch restrictions from GitHub Actions triggers
- Remove `--exclude-mail` flag from link checker configuration
- Remove branch restrictions from `rhiza_validate.yml` trigger
- Update `.rhiza/template-bundles.yml` to replace outdated workflow references with `.rhiza/semgrep.yml`
- Remove `rhiza_pip_audit.yml` from template-bundles.yml
- Remove `rhiza_security.yml` from template-bundles.yml
- Remove event-based restrictions from `rhiza_validate.yml` triggers
- Consolidate `license` and `semgrep` checks into `rhiza_validate.yml` and remove standalone workflows
## [0.8.18] - 2026-04-01

### 🚀 Features

- Add paper, presentations, and devcontainer docs from main

### 💼 Other

- Bump version 0.8.17 → 0.8.18

### 🚜 Refactor

- Move .semgrep.yml to .rhiza/semgrep.yml
- Consolidate CI workflows from main

### ⚙️ Miscellaneous Tasks

- Delete REPOSITORY_ANALYSIS.md
- Sync .pre-commit-config.yaml and GitLab CI from origin/main
- Remove deprecated `.claude/plan.md` and `.claude/quality.md` files
- Sync .gitlab/README.md from origin/main
## [0.8.17] - 2026-03-31

### 🚀 Features

- Exclude recipe/meta.yaml from check-yaml pre-commit hook (#931)
- Add lychee link check workflow and fix make security (#906)
- Add `license` make target to quality.mk for license compliance scanning (#914)

### 💼 Other

- Bump version 0.8.16 → 0.8.17
## [0.8.16] - 2026-03-22

### 🚀 Features

- Add rhiza_typecheck workflow with ty integration (#881)
- Add license compliance scan (make license + rhiza_license workflow) (#887)
- Add Semgrep static analysis (make semgrep + rhiza_semgrep workflow) (#888)
- Add issue templates to github template bundle (#890)

### 🐛 Bug Fixes

- Use `make validate` in CI so `post-validate` hooks fire (#884)

### 💼 Other

- Bump version 0.8.15 → 0.8.16
## [0.8.15] - 2026-03-21

### 💼 Other

- Bump version 0.8.14 → 0.8.15
## [0.8.14] - 2026-03-19

### 🚀 Features

- Add coverage badge generation via gh-pages (#863)
- Add XML coverage report output to test target (#871)

### 🐛 Bug Fixes

- *(ci)* Align artifact versions and guard badge steps on missing coverage
- *(ci)* Revert upload-artifact to v7 (v8 does not exist)

### 💼 Other

- Bump version 0.8.13 → 0.8.14

### ⚙️ Miscellaneous Tasks

- Replace deptry container with setup-uv action and update Makefile comments
- *(ci)* Replace container image with setup-uv action in security workflow
## [0.8.13] - 2026-03-17

### 🚀 Features

- Make book bundle standalone (#853)
- Extract benchmarks into its own bundle depending on tests (#855)
- Make marimo bundle depend on book bundle (#857)
- Re-add deprecated `materialize` target pointing to `sync` (#859)

### 💼 Other

- Bump version 0.8.12 → 0.8.13
## [0.8.12] - 2026-03-13

### 🚀 Features

- Add GitLab CI Marimo notebooks workflow (#843)

### 💼 Other

- Update UV image version 0.9.18 → 0.9.30 in marimo job template
- Bump version 0.8.11 → 0.8.12
## [0.8.11] - 2026-03-13

### 🐛 Bug Fixes

- Correct typos in .gitlab/workflows/rhiza_release.yml (#842)
- Resolve release workflow deprecation warnings (#840)

### 💼 Other

- Bump version 0.8.10 → 0.8.11
## [0.8.10] - 2026-03-13

### 💼 Other

- Bump version 0.8.9 → 0.8.10
## [0.8.9] - 2026-03-10

### 🚀 Features

- Add per-notebook artefact folders for rhiza_marimo runs (#832)

### 🐛 Bug Fixes

- Remove module docstring from rhiza.py so marimo recognises it as a notebook

### 💼 Other

- Bump version 0.8.8 → 0.8.9
## [0.8.8] - 2026-03-10

### 💼 Other

- Bump version 0.8.7 → 0.8.8
## [0.8.7] - 2026-03-09

### 💼 Other

- Bump version 0.8.6 → 0.8.7

### ⚙️ Miscellaneous Tasks

- Update rhiza.mk to use equality for version sync (#824)
## [0.8.6] - 2026-03-06

### 💼 Other

- Bump version 0.8.5 → 0.8.6
## [0.8.5] - 2026-02-27

### 💼 Other

- Bump version 0.8.4 → 0.8.5
## [0.8.4] - 2026-02-27

### 🚀 Features

- Upload book as downloadable workflow artifact (#793)

### 🐛 Bug Fixes

- Replace `uvx hatch build` with `uv build` in release workflows (#798)

### 💼 Other

- Bump version 0.8.3 → 0.8.4
## [0.8.3] - 2026-02-24

### 🐛 Bug Fixes

- Document subprocess security exceptions in test conftest files
- Handle pytest exit code 5 in hypothesis-test target

### 💼 Other

- Bump version 0.8.2 → 0.8.3

### ⚙️ Miscellaneous Tasks

- Move all type checking to ty (#786)
- Remove version field from template-bundles.yml (#788)
## [0.8.2] - 2026-02-23

### 🚀 Features

- Include hypothesis-test HTML report in book (#759)
- Add CodeFactor link to minibook with dynamic repo detection (#777)
- Enable blank issue creation (#779)

### 🐛 Bug Fixes

- Normalize tag version for version mismatch check (#729)
- Pin mkdocs<2.0 and mkdocs-material<10.0 to avoid MkDocs 2.0 incompatibility (#743)
- Add benchmark dependency to book target so Benchmarks panel is built
- Enable Mermaid diagram rendering in MkDocs documentation (#747)
- Include logo inside docs_dir so MkDocs copies it to the build
- Set hypothesis report title to "Hypothesis tests"
- Set hypothesis HTML report title via conftest hook
- Add security exception docs to stress and property conftest files

### 💼 Other

- Surface template bundles as the primary abstraction for template selection (#753)
- Bump version 0.8.1-rc.2 → 0.8.2

### 🚜 Refactor

- Simplify pytest HTML title hooks across test suites

### 📚 Documentation

- Reference rhiza-education in README, ROADMAP, and docs (#755)
- Add issue/PR templates and commit conventions
- Clarify the boundary between rhiza (template) and rhiza-tools (CLI) (#761)
- Fix rhiza-tools → rhiza-cli naming in README and GLOSSARY (#766)
- *(adr)* Backfill ADR-0002 through ADR-0009 (#769)
- Add ADR dropdown menu to mkdocs navigation (#771)
- Clarify tests/ as downstream blueprints, not Rhiza's own test suite (#774)
- Flesh out index.md and restructure mkdocs nav with dropdown sections (#776)
- Update ROADMAP.md to reflect v0.8.1-rc.2 and completed work (#781)

### 🛡️ Security

- Add SECURITY.md, secret scanning config, and update template bundles (#757)
## [0.8.1-rc.2] - 2026-02-17

### 💼 Other

- Bump version 0.8.1-rc.1 → 0.8.1-rc.2
## [0.8.0] - 2026-02-15

### 💼 Other

- Releasing
- Bump version 0.7.5 → 0.8.0

### ⚙️ Miscellaneous Tasks

- Update Renovate schedule to run nightly (#683)
## [0.7.5] - 2026-02-14

### 💼 Other

- Bump version 0.7.4 → 0.7.5
## [0.7.4] - 2026-02-14

### 💼 Other

- Bump version 0.7.3 → 0.7.4
## [0.7.3] - 2026-02-14

### 💼 Other

- Bump version 0.7.2 → 0.7.3
## [0.7.2] - 2026-02-14

### 💼 Other

- Sync template-bundles.yml version to 0.7.1
- Bump version 0.7.1 → 0.7.2

### 🚜 Refactor

- Move user customizations from .rhiza/make.d to root Makefile (#589)

### 📚 Documentation

- Consolidate infrastructure docs into .rhiza/docs/ (#638)

### ⚙️ Miscellaneous Tasks

- Make tests more DRY (#610)
## [0.7.1] - 2026-02-07

### 💼 Other

- Bump version 0.7.0 → 0.7.1

### 🚜 Refactor

- Migrate and reorganize test suite to .rhiza/tests with categorical structure (#542)

### ⚙️ Miscellaneous Tasks

- Add `.rhiza/template-bundles.yml` to define reusable template … (#545)
## [0.7.0] - 2026-02-05

### ⚙️ Miscellaneous Tasks

- Bump version v0.6.2 -> 0.7.0
## [0.6.2] - 2026-02-02

### 💼 Other

- Bump version 0.6.1 → 0.6.2
## [0.6.1] - 2026-01-26

### 🐛 Bug Fixes

- Incorrect values (#333)

### 💼 Other

- Remove unnecessary mo parameter from app cells in rhiza.py (#362)
- Bump version 0.6.0 → 0.6.1
## [0.6.0] - 2026-01-16

### 🐛 Bug Fixes

- Copilot install (#262)

### 💼 Other

- Bump version 0.5.0 → 0.6.0
## [0.5.0] - 2026-01-03

### ⚙️ Miscellaneous Tasks

- Bump version 0.4.1 -> 0.5.0
## [0.4.1] - 2026-01-01

### ⚙️ Miscellaneous Tasks

- Bump version to 0.4.1
## [0.4.0] - 2025-12-26

### ⚙️ Miscellaneous Tasks

- Bump version to 0.4.0
## [0.3.2] - 2025-12-25

### ⚙️ Miscellaneous Tasks

- Bump version to 0.3.2
## [0.3.1] - 2025-12-24

### 🐛 Bug Fixes

- *(deps)* Update dependency pre-commit to v4.5.1 (#67)

### ⚙️ Miscellaneous Tasks

- Bump version to 0.3.1

### 🛡️ Security

- Add workflow (#86)
## [0.3.0] - 2025-12-16

### ⚙️ Miscellaneous Tasks

- Bump version to 0.3.0
## [0.2.0] - 2025-12-16

### ⚙️ Miscellaneous Tasks

- Bump version to 0.2.0
## [0.1.0] - 2025-12-16

### ⚙️ Miscellaneous Tasks

- Bump version to 0.1.0
## [0.0.3] - 2025-12-16

### ⚙️ Miscellaneous Tasks

- Bump version to 0.0.3
## [0.0.2] - 2025-12-16

### ⚙️ Miscellaneous Tasks

- Bump version to 0.0.2
## [0.0.1] - 2025-12-16

### 🐛 Bug Fixes

- *(deps)* Update dependency marimo to v0.17.8 (#137)
- *(deps)* Update dependency pytest to v9 (#140)
- *(deps)* Update dependency pre-commit to v4.5.0 (#150)
- *(deps)* Update dependency marimo to v0.18.0 (#149)
- *(deps)* Update dependency marimo to v0.18.1 (#169)
- *(deps)* Update dependency marimo to v0.18.2 (#225)
- *(deps)* Update dependency marimo to v0.18.3 (#252)
- *(deps)* Update dependency pytest to v9.0.2 (#260)
- *(deps)* Update dependency marimo to v0.18.4 (#297)

### ⚙️ Miscellaneous Tasks

- Bump version to 0.9.0
- Bump version to 0.10.0
- Bump version to 0.0.1
