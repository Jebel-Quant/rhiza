# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and entries are generated from [Conventional Commits](https://www.conventionalcommits.org).

## [0.19.2] - 2026-06-16

### Bug Fixes
- *(paper)* Point GitHub paper workflow at docs/paper, matching paper.mk and GitLab (#1249)
- *(fuzzing)* Scope security-events:write to job level (#1250)
- *(scorecard)* Match reusable workflow top-level permissions to its job (#1251)
- *(gh-aw)* Recompile lock files for gh-aw v0.79.8 (#1254)

### Maintenance
- Chore(deps-dev)(deps-dev): bump hypothesis (#1252)
- Chore(deps)(deps): bump the github-actions group with 4 updates (#1253)

### Other Changes
- Skip fuzzing when the repo has no .clusterfuzzlite/ config (#1246)
- Rename Claude commands to rhiza_* and drop PUBLISH_COMPANION_BOOK toggle (#1248)

## [0.19.1] - 2026-06-15

### Dependencies
- *(deps)* Lock file maintenance (#1243)

### Other Changes
- Switch pre-commit secret scanner from gitleaks to betterleaks (#1242)
- Repair reusable-workflow caller stubs (concurrency deadlock + mutation perms) (#1244)
- Bump version 0.19.0 → 0.19.1

## [0.19.0] - 2026-06-14

### New Features
- *(github-tests)* Add opt-in mutation-testing workflow (#1198)
- *(github)* Stub remaining rhiza_* workflows and auto-pin stub versions (#1202)

### Dependencies
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.6.2 (#1239)

### Maintenance
- Install all extras in the lowest-deps compatibility job (#1199)
- Enforce mutation testing gate on pull requests (#1209)

### Other Changes
- Document `Private :: Do Not Upload` as release workflow PyPI kill-switch (#1194)
- Document classifier-driven CI Python matrix source of truth (#1195)
- Sync `cliff.toml` downstream and improve changelog signal quality (#1196)
- Disable noisy pytest live logging by default in shipped tests template (#1197)
- Enable Ruff ANN coverage in shipped template config (#1201)
- Add clean-tree verification to reusable CI test job (#1211)
- Publish computed mutation-score badge from `rhiza_mutation.yml` (#1210)
- Add /quality slash command for running quality gates (#1212)
- Add strict mypy as a second typecheck cross-check (#1208)
- Streamline release: single always-bumping `make release` (#1203)
- Revisit release: collapse publish into release, drop redundant changelog job, bump rhiza-tools floor (#1213)
- Add README/bundle sync test and template-bundles schema validation (#1216, #1217) (#1218)
- Add direct unit coverage for utility scripts (#1223)
- Gate docstring coverage for `.rhiza/utils` in pre-commit and `docs-coverage` (#1224)
- Restore typecheck + docs-coverage in /quality command (#1227)
- Make `security` fail closed on missing `src` (#1226)
- Rename the /quality command to /rhiza (#1229)
- Sign releases: stage SBOM Sigstore attestation as a release signature asset (#1231)
- Silence deptry "Assuming module name" warnings via package_module_name_map (#1233)
- Move synced utils' tests into .rhiza/tests so they travel downstream (#1230)
- Skip pre-commit hook install when core.hooksPath is set (#1234)
- Move fuzz harnesses from root fuzz/ to tests/fuzz/ (#1232)
- Extend docs-coverage to the test packages (tests/, .rhiza/tests/) (#1235)
- Add rhiza-test and validate gates to the /rhiza command (#1236)
- Remove make validate from the /rhiza command (#1237)
- Fix validation job failure by updating typecheck dry-run assertions (#1228)
- Ship a downstream /rhiza quality command in the core bundle (#1238)
- Strip SLSA provenance from dist/ before PyPI publish (#1240)
- Bump version 0.18.10 → 0.19.0

## [0.18.10] - 2026-06-12

### New Features
- Add cliff.toml, make changelog target, PR + discussion templates (#1166)

### Bug Fixes
- *(make)* Sync bundles/core/.rhiza/rhiza.mk with root ci-os-matrix recipe change (#1171)
- Catch IndentationError in suppression_audit scan_file to prevent fuzzer crash (#1177)

### Documentation
- Fix dead links, stale bundle docs, and add missing CONFIG.md (#1147)
- Gate prose-level drift and remove Last Updated stamps (#1154)
- Add 'Why not copier/cruft' design rationale (#1162)

### Dependencies
- *(deps)* Update jebel-quant/rhiza action to v0.18.9 (#1173)
- *(deps)* Lock file maintenance (#1175)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.17 (#1181)
- *(deps)* Combine Renovate updates #1182–#1187 (binary merge) (#1188)

### Maintenance
- Add concurrency groups and enforce precise action pinning (#1148)
- Commit gh-aw compiled lock files and enforce them in CI (#1161)

### Other Changes
- Add gitleaks, remove piped installers, widen shellcheck (#1149)
- Cache shell-completion targets and add a Windows/WSL quick-start (#1155)
- Enable ruff A/ARG/BLE/PIE, gate duplicate make targets, add bundle checklist (#1160)
- Correct SECURITY.md release claims and gate them against reality (#1163)
- Add OSSF Scorecard workflow and README badge (#1164)
- Cherry-pick safe StepSecurity hardening from #1167 (#1168)
- Complete StepSecurity workflow hardening (SHA-pin all workflows) (#1170)
- Raise OpenSSF Scorecard (token-permissions, signed-releases, branch-protection) (#1172)
- Remove 'github-actions' from Renovate config (#1174)
- Propagate least-privilege permissions to bundle templates (#1178)
- Align branch-protection ruleset with applied state (#1179)
- Fix `book` workflow failure caused by editable install package discovery (#1180)
- Harden branch-protection ruleset and prep Code-Review/CII (#1189)
- Bump version 0.18.9 → 0.18.10

## [0.18.9] - 2026-06-10

### Dependencies
- *(deps)* Lock file maintenance (#1144)

### Maintenance
- Chore(deps)(deps): bump jebel-quant/rhiza in the github-actions group (#1145)

### Other Changes
- Fail fast on native Windows shells and run Windows CI tests under bash (#1146)
- Bump version 0.18.8 → 0.18.9

## [0.18.8] - 2026-06-06

### Other Changes
- Update workflow references to version 0.18.7
- Bump version 0.18.7 → 0.18.8

## [0.18.7] - 2026-06-06

### Bug Fixes
- *(ci)* Install chromium in GitLab CI jobs for kaleido/plotly image export
- *(ci)* Use versioned remote ref for configure-git-auth action (#1143)

### Other Changes
- Bump version 0.18.6 → 0.18.7

## [0.18.6] - 2026-06-04

### Dependencies
- *(deps)* Lock file maintenance (#1140)

### Maintenance
- Chore(deps-dev)(deps-dev): bump plotly in the python-dependencies group (#1142)
- Chore(deps)(deps): bump jebel-quant/rhiza in the github-actions group (#1141)

### Other Changes
- Add optional, toggleable grayskull-based conda recipe generation to release pipeline (#1137)
- Bump version 0.18.5 → 0.18.6

## [0.18.5] - 2026-05-31

### New Features
- *(devcontainer)* Link github-devcontainer overlay via recommends and add bundle combination tests (#1129)
- Add mutation testing via mutmut (#1138)

### Maintenance
- Skip book workflow on forks
- *(tests)* Move rhiza-specific tests to correct locations (#1139)
- Enforce monotonic release tags and align pyproject sync tests (#1133)

### Other Changes
- Delete bundles/core/pyproject.toml.template (#1130)
- Bump version 0.18.4 → 0.18.5

## [0.18.4] - 2026-05-28

### Maintenance
- Move test_lfs.py to lfs bundle, test_gh_aw/github targets to gh-aw bundle
- Move test-pyproject target and test file to tests bundle

### Other Changes
- Bump version 0.18.3 → 0.18.4

## [0.18.3] - 2026-05-28

### Bug Fixes
- Resolve Windows CI failures and reduce LFS skip noise
- Comment out optional_dirs check in test_root_contains_expected_directories
- Sync bundle copy of test_project_layout.py with root .rhiza/

### Maintenance
- Add lint dependency group check to test-pyproject
- Move rhiza-only tests from .rhiza/tests/ to tests/
- Delete test_lfs_structure.py, fold existence checks into integration
- Delete test_completions.py and test_config_files.py from structure/

### Other Changes
- Bump version 0.18.2 → 0.18.3

## [0.18.2] - 2026-05-28

### New Features
- Group bundles by platform in explain-bundles output

### Maintenance
- Align core bundle doctor.mk with .rhiza version
- Sync ty version constraint in core bundle with .rhiza
- Add bundle-root sync check and fix all stale bundle files

### Other Changes
- Bump version 0.18.1 → 0.18.2

## [0.18.1] - 2026-05-28

### Maintenance
- Rename pyproject.toml to .template and centralize test fixtures (#1125)

### Other Changes
- Bump version 0.18.0 → 0.18.1

## [0.18.0] - 2026-05-28

### New Features
- *(ci)* Add lowest-deps job to rhiza_ci workflow
- *(ci)* Run typecheck job across full Python version matrix
- Add make explain-bundles onboarding target

### Bug Fixes
- Quote pre-commit entry to fix YAML syntax error in no-rej-files hook
- Bump pyyaml lower bound to 6.0.1 to fix lowest-deps build failure
- *(ci)* Install .rhiza/requirements in lowest-deps job
- *(ci)* Run uv sync before pip install in lowest-deps job
- *(ci)* Pass GITLEAKS_LICENSE through reusable CI workflow (#1106)

### Documentation
- Add comprehensive repository quality analysis
- Document GNU Make requirement and add BSD make guard
- Add bundle dependency map to glossary (#1085)
- Add worked “new bundle” tutorial to EXTENDING_RHIZA (#1102)
- Revisit README and document downstream expectations (#1124)

### Dependencies
- *(deps)* Introduce uv lint/test/docs groups for lightweight installs (#1117)

### Maintenance
- Enforce required Renovate manager coverage in validation test
- Add end-to-end downstream sync test for minimal git repo (#1087)
- Add pytest-xdist to test requirements
- *(bundles)* Add bundle×platform compatibility matrix (144 parametrized cases) (#1103)
- Add global pytest timeout and sync failure-mode coverage (#1119)
- Remove stale Claude agent worktree references

### Other Changes
- Revert "docs: add comprehensive repository quality analysis"
- Add scoped shellcheck pre-commit hook for `.rhiza/utils` scripts (#1084)
- Formalize bundle dependency DAG validation (#1101)
- Add GitHub/GitLab CI parity smoke test (#1099)
- [WIP] Document global-patch propagation pattern for cross-bundle changes (#1100)
- [WIP] Add CI step to automate Bandit suppression review and simplify suppression audit (#1104)
- Revert "fix(ci): pass GITLEAKS_LICENSE through reusable CI workflow (#1106)"
- Parallelize `make test` and bound Marimo notebook runtime (#1107)
- Add `make doctor` diagnostics and bundle-sync troubleshooting guide (#1114)
- Add bundle invariant test for duplicate file inclusion (#1121)
- Enforce per-job time budgets and standardize cache keys (#1118)
- Add docs build cache/timing and benchmark baseline workflow (#1123)
- Add core pyproject template and enforce minimum pyproject structure in downstream validation (#1122)
- Bump version 0.17.0 → 0.18.0

## [0.17.0] - 2026-05-27

### Documentation
- *(github)* Explain why rhiza_release cannot use a workflow stub

### Other Changes
- Bump version 0.16.0 → 0.17.0

## [0.16.0] - 2026-05-27

### New Features
- Add workflow_call support to rhiza_release workflow
- Add workflow_call support to weekly and gh-aw-validate workflows

### Bug Fixes
- *(book)* Run docs server via uv in `serve` target (#1074)

### Maintenance
- Add CodeFactor config to exclude bundles/ from analysis
- Add .codefactor.yml to core bundle
- Remove .codefactor.yml from core bundle

### Other Changes
- Bump version 0.15.3 → 0.16.0

## [0.15.3] - 2026-05-26

### Bug Fixes
- Pin configure-git-auth action to v0.15.2 instead of @main
- Downgrade setup-uv from v8.1.0 to v7.6.0

### Other Changes
- Bump version 0.15.2 → 0.15.3

## [0.15.2] - 2026-05-26

### Bug Fixes
- Strip whitespace from PYTHON_VERSION read from .python-version

### Other Changes
- Bump version 0.15.1 → 0.15.2

## [0.15.1] - 2026-05-26

### Bug Fixes
- Skip test_bundles_directory_exists in downstream repos
- Correct release workflow trigger assertions in test_workflow_stubs

### Maintenance
- Register kaleido pytest mark in pytest.ini
- Add 75 new tests across bundle content, combinations, and sync

### Other Changes
- Bump version 0.15.0 → 0.16.1
- Bump version 0.15.0 → 0.15.1

## [0.15.0] - 2026-05-26

### New Features
- Overhaul bundle structure, testing, and GitHub workflows (#1072)

### Other Changes
- Bump version 0.14.0 → 0.15.0

## [0.14.0] - 2026-05-25

### New Features
- Introduce bundle-centric directory layout (#1071)

### Other Changes
- Bump version 0.13.3 → 0.14.0

## [0.13.3] - 2026-05-25

### Bug Fixes
- Use absolute action reference for configure-git-auth
- Use absolute action reference for configure-git-auth
- Use absolute action reference for configure-git-auth
- Remove tests asserting unexpanded reusable workflow jobs (#1070)

### Other Changes
- Remove .github/actions from template bundles
- Bump version 0.13.2 → 0.13.3

## [0.13.2] - 2026-05-25

### New Features
- Add workflow_call support and github-specific workflow bundles

### Other Changes
- Delete .github/workflows/rhiza_quality.yml (#1069)
- Bump version 0.13.1 → 0.13.2

## [0.13.1] - 2026-05-25

### Bug Fixes
- Add github as dependency of github-book, github-marimo, github-tests

### Maintenance
- Add bundle reliability tests and fix book.mk ownership conflict (#1068)

### Other Changes
- Bump version 0.13.0 → 0.13.1

## [0.13.0] - 2026-05-25

### New Features
- Add workflow stubs and granular gitlab/github bundles

### Bug Fixes
- Handle {source, dest} dict entries in template bundle tests

### Other Changes
- Bump version 0.12.0 → 0.13.0

## [0.12.0] - 2026-05-24

### New Features
- Remove .github/workflows from template bundles

### Other Changes
- Bump version 0.11.0 → 0.12.0

## [0.11.3] - 2026-05-24

### New Features
- Add workflow_call trigger to support reusable workflow usage
- Add workflow_call trigger with direct/create-pr inputs

## [0.11.2] - 2026-05-24

### New Features
- Add workflow_call trigger to support reusable workflow usage
- Add workflow_call trigger to support reusable workflow usage

## [0.11.1] - 2026-05-24

### New Features
- Add workflow_call trigger to support reusable workflow usage

### Bug Fixes
- Remove tests for generate-matrix/test jobs no longer in ci workflow

## [0.11.0] - 2026-05-24

### New Features
- Add RHIZA_SYNC_SCHEDULE variable to override default sync cron (#955)

### Dependencies
- *(deps)* Update github/codeql-action action to v4.36.0 (#1063)
- *(deps)* Update docker/setup-buildx-action action to v4.1.0 (#1062)
- *(deps)* Update docker/login-action action to v4.2.0 (#1061)

### Other Changes
- Update template-bundles and bump version 0.12.1 → 0.14.1
- Bump version 0.10.9 → 0.11.0

## [0.10.9] - 2026-05-22

### Other Changes
- Fix missing uv install in update-changelog CI job
- Bump version 0.10.8 → 0.10.9

## [0.10.8] - 2026-05-22

### New Features
- Update CHANGELOG.md on every release via git-cliff (#1052)

### Bug Fixes
- *(docker)* Upgrade pip to 26.1 to fix CVE-2026-6357 (#1058)

### Dependencies
- *(deps)* Lock file maintenance (#1049)
- *(deps)* Update dependency astral-sh/uv to v0.11.16 (#1053)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.14 (#1054)
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.4.0 (#1056)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.16 (#1055)
- *(deps)* Update ghcr.io/devcontainers/features/docker-in-docker docker tag to v3 (#1057)

### Maintenance
- Chore(deps-dev)(deps-dev): bump numpy in the python-dependencies group (#1050)
- Generate CHANGELOG.md with git-cliff

### Other Changes
- Fix flaky CI uv setup by retrying failed install once (#1060)
- Bump version 0.10.7 → 0.10.8

## [0.10.7] - 2026-05-17

### New Features
- *(ci)* Parameterize CI OS matrix via RHIZA_CI_OS_MATRIX (#1040)

### Dependencies
- *(deps)* Update dependency astral-sh/uv to v0.11.11 (#1036)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.11 (#1037)
- *(deps)* Update github/codeql-action action to v4.35.4 (#1039)
- *(deps)* Update dependency astral-sh/uv to v0.11.12 (#1041)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.12 (#1042)
- *(deps)* Lock file maintenance (#1043)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.13 (#1047)
- *(deps)* Update dependency astral-sh/uv to v0.11.14 (#1045)
- *(deps)* Update github/codeql-action action to v4.35.5 (#1046)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.14 (#1048)

### Maintenance
- Chore(deps-dev)(deps-dev): bump the python-dependencies group with 2 updates (#1044)

### Other Changes
- Remove 'make coverage-badge'
- Bump version 0.10.6 → 0.10.7

## [0.10.6] - 2026-05-06

### New Features
- Introduce layered bundle/profile model with local-first bundles (#1028)

### Bug Fixes
- *(tests)* Skip GitHub-specific security checks when github bundle not included (#1027)

### Dependencies
- *(deps)* Lock file maintenance (#1029)
- *(deps)* Update github/codeql-action action to v4.35.3 (#1032)
- *(deps)* Update dependency astral-sh/uv to v0.11.10 (#1031)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.37.2 (#1034)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.10 (#1033)

### Maintenance
- Chore(deps-dev)(deps-dev): bump marimo in the python-dependencies group (#1030)
- Restore renovate.json

### Other Changes
- Delete renovate.json
- Bump version 0.10.5 → 0.10.6

## [0.10.5] - 2026-04-29

### New Features
- *(ci)* Add coverage regex to ci:test job
- Add no-python-cache-files local pre-commit hook (#1026)

### Dependencies
- *(deps)* Update dependency astral-sh/uv to v0.11.8 (#1021)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.8 (#1023)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.12 (#1022)
- *(deps)* Update aquasecurity/trivy-action action to v0.36.0 (#1024)
- *(deps)* Update ghcr.io/devcontainers/features/node docker tag to v2 (#1025)

### Other Changes
- Bump version 0.10.4 → 0.10.5

## [0.10.4] - 2026-04-27

### New Features
- Move semgrep.yml from .github to .rhiza (#1020)

### Bug Fixes
- Ensure _book output dir exists before touching .nojekyll
- *(book)* Pin zensical>=0.0.36 to avoid stale CI cache resolving broken older version

### Dependencies
- *(deps)* Lock file maintenance (#1018)

### Other Changes
- Bump python-dotenv to version 1.2.2 (#1017)
- Bump version 0.10.3 → 0.10.4

## [0.10.3] - 2026-04-25

### New Features
- *(core)* Add .rhiza/utils to core bundle

### Bug Fixes
- *(security)* Warn on tooling CVEs, fail only on runtime dep vulnerabilities (#1016)

### Other Changes
- Remove link-check job from rhiza_quality.yml (for gitlab)
- Remove weekly link-check job from CI pipeline (for gitlab)
- Remove tree command from book.mk
- Bump version 0.10.2 → 0.10.3

## [0.10.2] - 2026-04-22

### Bug Fixes
- *(ci)* Use git lfs install --force to avoid hook conflict on runners
- *(ci)* Use git lfs install --force to avoid hook conflict on runners

### Dependencies
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.11 (#1012)
- *(deps)* Update astral-sh/setup-uv action to v8.1.0 (#1013)
- *(deps)* Lock file maintenance (#1014)

### Maintenance
- Replace removed workflows with current rhiza equivalents
- Chore(deps-dev)(deps-dev): bump marimo in the python-dependencies group (#1015)

### Other Changes
- Move semgrep.yml to test bundle section
- Update mkdocs
- Bump version 0.10.1 → 0.10.2

## [0.10.1] - 2026-04-18

### Other Changes
- Remove .rhiza/docs from template bundles
- Remove mkdocs and related dependencies
- Remove custom targets comment from Makefile
- Update MKDOCS_EXTRA_PACKAGES in Makefile
- Remove README.md from template bundles
- Skip gh-aw and github target tests when their .mk files are missing
- Adr revisited
- Adr revisited
- No longer mkdocs
- Move coverage badge into book build; drop gh-pages branch usage
- Remove rhiza_benchmarks.yml and gh-pages benchmark storage
- Fix coverage-badge test assertion to match genbadge[coverage] invocation
- Change Standalone status for GitHub and GitLab bundles
- Accept 504 Gateway Timeout in lychee link checker
- Cleaner github vs gh-aw
- Remove duplicate .rhiza/semgrep.yml (canonical copy is .github/semgrep.yml)
- Bump version 0.10.0 → 0.10.1

## [0.10.0] - 2026-04-17

### New Features
- Add .bandit INI file as single source of truth for bandit configuration (#997)

### Bug Fixes
- Fix nav report paths to match _tests folder names
- Fix README rendering in MkDocs and remove persistent nav sections

### Documentation
- Fix template documentation issues from Copilot review (#999)

### Dependencies
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.3.3 (#995)
- *(deps)* Update dependency astral-sh/uv to v0.11.7 (#1000)
- *(deps)* Update github/codeql-action action to v4.35.2 (#1001)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.7 (#1002)

### Maintenance
- Add tests for rhiza_weekly.yml jobs and Makefile targets (#994)
- Move `adr` target from root Makefile to `.rhiza/make.d/gh-aw.mk` (#1011)

### Other Changes
- Interrogate
- Remove pdoc from documentation dependencies
- Replace `uvx uv run` with `uv run --script` in marimo workflow (#1004)
- Change default AI model to claude-sonnet-4.6 (#1005)
- Add mike dependency to documentation requirements (#1006)
- Add versioning configuration to mkdocs (#1007)
- Add zensical>=0.0.33 to docs requirements
- Remove mkdocs-build, mkdocs-serve, and mkdocs targets from book.mk
- Update tests to reflect removal of mkdocs-build, mkdocs-serve, mkdocs targets
- Add ROOT variable to book.mk via git rev-parse --show-toplevel
- Add serve target to book.mk using Python's built-in HTTP server
- Simplify book.mk: replace _MKDOCS_CFG with inline \${ROOT}/mkdocs.yml
- Remove nav section from mkdocs-base.yml
- No need for notebooks.md
- No need for notebooks.md
- No need for notebooks.md
- No need for report.md
- Simplify _book-reports to copy _tests directly into docs/reports
- Add theme name: material to fix CI build
- Clean up mkdocs.yml by removing duplicates
- Replace lucide toggle icons with material icons for CI compatibility
- Update mkdocs.yml
- Switch book build to use zensical build command
- Bump version 0.9.5 → 0.10.0

## [0.9.5] - 2026-04-13

### Other Changes
- Add CI job to catch unresolved .rej patch files
- Extend conflict check to also catch merge conflict markers
- Delete .github/ISSUE_TEMPLATE/config.yml
- Don't copy over excessive documentation from rhiza
- Bump version 0.9.4 → 0.9.5

## [0.9.4] - 2026-04-13

### Bug Fixes
- Fixing a missing book makefile

### Other Changes
- Index fed by README
- Bump version 0.9.3 → 0.9.4

## [0.9.3] - 2026-04-13

### New Features
- *(core)* Add important docs files and folders to core bundle (#991)

### Dependencies
- *(deps)* Lock file maintenance (#985)

### Other Changes
- Enhance book build process with mkdocs config detection
- Delete docs/SECURITY.md
- Remove docs/SECURITY.md from template-bundles.yml
- Add docs/mkdocs-base.yml base config with INHERIT (#986)
- Revise Rhiza documentation to remove old content (#987)
- Reorganise docs/ into subdirectories by topic (#988)
- Docs (#989)
- Bump version 0.9.2 → 0.9.3

## [0.9.2] - 2026-04-12

### Dependencies
- *(deps)* Update actions/upload-artifact action to v7.0.1 (#977)
- *(deps)* Update actions/upload-pages-artifact action to v5 (#982)
- *(deps)* Update astral-sh/setup-uv action to v8 (#983)
- *(deps)* Update peter-evans/create-pull-request action to v8.1.1 (#979)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.6 (#981)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.10 (#980)
- *(deps)* Update dependency astral-sh/uv to v0.11.6 (#978)

### Other Changes
- Copilot/add GitHub and gitlab validation (#984)
- Bump version 0.9.1 → 0.9.2

## [0.9.1] - 2026-04-12

### New Features
- *(docs.mk)* Add MKDOCS_EXTRA_PACKAGES to extend uvx package list without editing template (#975)
- *(gitlab)* Bring GitLab rhiza_validate to parity with GitHub Actions equivalent (#952)

### Bug Fixes
- *(book)* Use MARIMO_FOLDER in _book-notebooks, fix double-nested links, narrow .gitignore (#973)

### Dependencies
- *(deps)* Lock file maintenance (#971)

### Other Changes
- Remove security and quality scan targets
- Delete book/marimo/notebooks directory (#976)
- Bump version 0.9.0 → 0.9.1

## [0.9.0] - 2026-04-03

### Dependencies
- *(deps)* Update dependency astral-sh/uv to v0.11.3 (#961)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.9 (#962)
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.3.2 (#964)

### Maintenance
- Merge origin/main into main, keep workflow consolidation from release/v0.8.21

### Other Changes
- Update rhiza_sync.yml
- Bump version 0.8.21 → 0.9.0

## [0.8.21] - 2026-04-03

### New Features
- Add suppression-audit makefile target (#896)
- Use git-cliff for release notes in rhiza_release.yml (#901)
- Add lychee link check workflow and fix make security (#906)
- Add `license` make target to quality.mk for license compliance scanning (#914)
- Add rhiza_paper.yml — LaTeX paper compilation workflow (#920)
- Exclude recipe/meta.yaml from check-yaml pre-commit hook (#931)
- Relocate Marimo notebooks to docs/notebooks (#939)
- Add .gitlab/workflows/rhiza_quality.yml as GitLab equivalent of GitHub quality workflow (#950)
- Add `license` make target to quality.mk for license compliance scanning (#914)

### Bug Fixes
- Analyse-repo target uses Claude CLI instead of Copilot CLI (#902)
- Resolve broken file references in README and template bundles
- Update rhiza_paper.yml paths from paper/ to docs/paper/

### Documentation
- Update requirements README to reflect current dependencies
- Clean up README formatting and remove outdated references

### Dependencies
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.3.1 (#891)
- *(deps)* Lock file maintenance (#892)
- *(deps)* Lock file maintenance (#894)
- *(deps)* Update dependency astral-sh/uv to v0.11.2 (#924)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.37.1 (#923)
- *(deps)* Update actions/deploy-pages action to v5 (#926)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.8 (#922)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.2 (#925)
- *(deps)* Lock file maintenance (#953)
- *(deps)* Update astral-sh/setup-uv action to v8 (#968)
- *(deps)* Update github/codeql-action action to v4.35.1 (#967)
- *(deps)* Update pre-commit hook rhysd/actionlint to v1.7.12 (#965)
- *(deps)* Update docker/login-action action to v4.1.0 (#966)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.3 (#963)

### Maintenance
- Remove branch-based trigger restrictions from rhiza_sync workflow
- Sync .github/agents from tschm/jquantstats
- Consolidate root-level community files into .github/ (#938)
- Consolidate individual rhiza_ CI workflows into rhiza_quality and rhiza_validate (#940)
- Move paper into docs/paper (#945)
- Move presentation/ folder to docs/presentations/ (#948)
- Merge main into release/v0.8.21, keep workflow consolidation

### Other Changes
- Delete .rhiza/tests/integration/test_marimushka.py (#915)
- Add mkdocs and related dependencies to docs.txt (#916)
- Update uv version and CI configuration for multiple OS (#921)
- Mkdocs2 (#917)
- Delete REPOSITORY_ANALYSIS.md
- Delete .claude directory
- Update ruff.toml to change notebook path pattern (#941)
- Delete .github/README.md
- Move notebooks into docs/notebooks (#943)
- Delete book directory (#946)
- Bump version 0.8.16 → 0.8.17
- Merge remote-tracking branch 'origin/main' into release/v0.8.21
- Update README.md
- Update .github/workflows/rhiza_sync.yml
- Update Makefile
- Merge branch 'main' into release/v0.8.21
- Merge branch 'main' into release/v0.8.21
- Merge branch 'main' into release/v0.8.21
- Bump version 0.8.20 → 0.8.21

## [0.8.20] - 2026-04-02

### Bug Fixes
- Align rhiza_weekly.yml comment with actual triggers
- Add pull_request trigger and fix on: syntax in rhiza_ci.yml

### Documentation
- Fix bibliography formatting and add bibtex to paper build

### Maintenance
- Update semgrep config path to .rhiza/semgrep.yml
- Consolidate GitHub Actions workflows
- Consolidate GitLab CI workflows to mirror GitHub Actions structure

### Other Changes
- Update .github/workflows/rhiza_sync.yml
- Bump version 0.8.19 → 0.8.20

## [0.8.19] - 2026-04-01

### New Features
- Add GitLab CI workflows for link checking and paper compilation

### Bug Fixes
- Update broken markdown links to correct file paths

### Maintenance
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

### Other Changes
- Paper.mk
- Bump version 0.8.18 → 0.8.19

## [0.8.18] - 2026-04-01

### New Features
- Add paper, presentations, and devcontainer docs from main

### Maintenance
- Move .semgrep.yml to .rhiza/semgrep.yml
- Delete REPOSITORY_ANALYSIS.md
- Consolidate CI workflows from main
- Sync .pre-commit-config.yaml and GitLab CI from origin/main
- Remove deprecated `.claude/plan.md` and `.claude/quality.md` files
- Sync .gitlab/README.md from origin/main

### Other Changes
- Bump version 0.8.17 → 0.8.18

## [0.8.17] - 2026-03-31

### New Features
- Exclude recipe/meta.yaml from check-yaml pre-commit hook (#931)
- Add lychee link check workflow and fix make security (#906)
- Add `license` make target to quality.mk for license compliance scanning (#914)

### Dependencies
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.8 (#922)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.11.2 (#925)
- *(deps)* Update actions/deploy-pages action to v5 (#926)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.37.1 (#923)
- *(deps)* Update dependency astral-sh/uv to v0.11.2 (#924)

### Other Changes
- Update uv version and CI configuration for multiple OS (#921)
- Delete .rhiza/tests/integration/test_marimushka.py (#915)
- Bump version 0.8.16 → 0.8.17

## [0.8.16] - 2026-03-22

### New Features
- Add rhiza_typecheck workflow with ty integration (#881)
- Add license compliance scan (make license + rhiza_license workflow) (#887)
- Add Semgrep static analysis (make semgrep + rhiza_semgrep workflow) (#888)
- Add issue templates to github template bundle (#890)

### Bug Fixes
- Use `make validate` in CI so `post-validate` hooks fire (#884)

### Other Changes
- Remove serial notebook testing from .rhiza/tests (#879)
- Update .gitignore to exclude output directory (#882)
- Feat/license compliance (#889)
- Update discussion URL in issue template config
- Bump version 0.8.15 → 0.8.16

## [0.8.15] - 2026-03-21

### Dependencies
- *(deps)* Update github/codeql-action action to v4.34.1 (#877)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.12 (#876)
- *(deps)* Update dependency astral-sh/uv to v0.10.12 (#874)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.7 (#875)

### Other Changes
- Remove page link cards from minibook template (#872)
- Claude/remove doc links lg f ct (#873)
- Bump version 0.8.14 → 0.8.15

## [0.8.14] - 2026-03-19

### New Features
- Add coverage badge generation via gh-pages (#863)
- Add XML coverage report output to test target (#871)

### Bug Fixes
- *(ci)* Align artifact versions and guard badge steps on missing coverage
- *(ci)* Revert upload-artifact to v7 (v8 does not exist)

### Maintenance
- Chore(deps-dev)(deps-dev): bump marimo in the python-dependencies group (#860)
- Replace deptry container with setup-uv action and update Makefile comments
- *(ci)* Replace container image with setup-uv action in security workflow

### Other Changes
- Skip coverage-badge if there is no src folder (#865)
- Bump version 0.8.13 → 0.8.14

## [0.8.13] - 2026-03-17

### New Features
- Make book bundle standalone (#853)
- Extract benchmarks into its own bundle depending on tests (#855)
- Make marimo bundle depend on book bundle (#857)
- Re-add deprecated `materialize` target pointing to `sync` (#859)

### Dependencies
- *(deps)* Update dependency astral-sh/uv to v0.10.10 (#844)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.10 (#845)
- *(deps)* Lock file maintenance (#846)
- *(deps)* Update ncipollo/release-action action to v1.21.0 (#847)
- *(deps)* Update dependency astral-sh/uv to v0.10.11 (#848)
- *(deps)* Update astral-sh/setup-uv action to v7.6.0 (#850)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.11 (#849)
- *(deps)* Update github/codeql-action action to v4.33.0 (#851)

### Other Changes
- Bump version 0.8.12 → 0.8.13

## [0.8.12] - 2026-03-13

### New Features
- Add GitLab CI Marimo notebooks workflow (#843)

### Other Changes
- Update UV image version 0.9.18 → 0.9.30 in marimo job template
- Bump version 0.8.11 → 0.8.12

## [0.8.11] - 2026-03-13

### Bug Fixes
- Correct typos in .gitlab/workflows/rhiza_release.yml (#842)
- Resolve release workflow deprecation warnings (#840)

### Other Changes
- Bump version 0.8.10 → 0.8.11

## [0.8.10] - 2026-03-13

### Dependencies
- *(deps)* Update astral-sh/setup-uv action to v7.4.0 (#833)
- *(deps)* Update actions/download-artifact action to v8.0.1 (#834)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.6 (#835)
- *(deps)* Update astral-sh/setup-uv action to v7.5.0 (#836)

### Other Changes
- Delete book/marimo/notebooks/demo.py (#837)
- Bump version 0.8.9 → 0.8.10

## [0.8.9] - 2026-03-10

### New Features
- Add per-notebook artefact folders for rhiza_marimo runs (#832)

### Bug Fixes
- Remove module docstring from rhiza.py so marimo recognises it as a notebook

### Maintenance
- Chore(deps-dev)(deps-dev): bump numpy in the python-dependencies group (#830)

### Other Changes
- Bump version 0.8.8 → 0.8.9

## [0.8.8] - 2026-03-10

### Dependencies
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.9 (#828)
- *(deps)* Update dependency astral-sh/uv to v0.10.9 (#827)
- *(deps)* Update aquasecurity/trivy-action action to v0.35.0 (#829)

### Other Changes
- Remove emojis from session hooks, use text error codes (#826)
- Analysis
- Bump version 0.8.7 → 0.8.8

## [0.8.7] - 2026-03-09

### Dependencies
- *(deps)* Lock file maintenance (#823)

### Maintenance
- Update rhiza.mk to use equality for version sync (#824)

### Other Changes
- Rename workflow from 'Renovate Rhiza Template Sync' to 'Rhiza Template Sync'
- Update Rhiza version from 0.11.6 to 0.12.1
- Bump version 0.8.6 → 0.8.7

## [0.8.6] - 2026-03-06

### Dependencies
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.7 (#811)
- *(deps)* Update astral-sh/setup-uv action to v7.3.1 (#810)
- *(deps)* Lock file maintenance (#812)
- *(deps)* Update dependency astral-sh/uv to v0.10.8 (#815)
- *(deps)* Update docker/setup-buildx-action action to v4 (#821)
- *(deps)* Update pre-commit hook igorshubovych/markdownlint-cli to v0.48.0 (#819)
- *(deps)* Update github/codeql-action action to v4.32.6 (#816)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.8 (#818)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.5 (#817)
- *(deps)* Update docker/login-action action to v4 (#820)

### Maintenance
- Chore(deps)(deps): bump aquasecurity/trivy-action (#814)
- Chore(deps-dev)(deps-dev): bump plotly in the python-dependencies group (#813)

### Other Changes
- Bump version to 0.11.6 (#809)
- Revisit bundles (#822)
- Nvm update
- Failed bump/release
- Bump version 0.8.5 → 0.8.6

## [0.8.5] - 2026-02-27

### Dependencies
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.4 (#802)
- *(deps)* Update actions/upload-artifact action to v4.6.2 (#800)
- *(deps)* Update pre-commit hook pycqa/bandit to v1.9.4 (#804)
- *(deps)* Update actions/attest-build-provenance action to v4 (#806)
- *(deps)* Update actions/attest-sbom action to v4 (#807)
- *(deps)* Update github artifact actions (#808)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.37.0 (#805)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.6 (#803)
- *(deps)* Update dependency astral-sh/uv to v0.10.7 (#801)

### Other Changes
- Bump version 0.8.4 → 0.8.5

## [0.8.4] - 2026-02-27

### New Features
- Upload book as downloadable workflow artifact (#793)

### Bug Fixes
- Replace `uvx hatch build` with `uv build` in release workflows (#798)

### Other Changes
- Remove 'Synced with Rhiza' badge (#796)
- Replace `uvx rhiza materialize` with `uvx rhiza sync` (#795)
- Update Rhiza version from 0.11.2 to 0.11.5 (#799)
- Bump version 0.8.3 → 0.8.4

## [0.8.3] - 2026-02-24

### Bug Fixes
- Document subprocess security exceptions in test conftest files
- Handle pytest exit code 5 in hypothesis-test target

### Maintenance
- Move all type checking to ty (#786)
- Remove version field from template-bundles.yml (#788)
- Chore(deps)(deps): bump aquasecurity/trivy-action (#789)

### Other Changes
- Missing gh-aw.mk in template-bundle
- Update Rhiza version from 0.11.0 to 0.11.2
- Add _site to .gitignore (#791)
- Bump version 0.8.2 → 0.8.3

## [0.8.2] - 2026-02-23

### New Features
- Include hypothesis-test HTML report in book (#759)
- Add CodeFactor link to minibook with dynamic repo detection (#777)
- Enable blank issue creation (#779)

### Bug Fixes
- Normalize tag version for version mismatch check (#729)
- Pin mkdocs<2.0 and mkdocs-material<10.0 to avoid MkDocs 2.0 incompatibility (#743)
- Add benchmark dependency to book target so Benchmarks panel is built
- Enable Mermaid diagram rendering in MkDocs documentation (#747)
- Include logo inside docs_dir so MkDocs copies it to the build
- Set hypothesis report title to "Hypothesis tests"
- Set hypothesis HTML report title via conftest hook
- Add security exception docs to stress and property conftest files

### Documentation
- Reference rhiza-education in README, ROADMAP, and docs (#755)
- Add issue/PR templates and commit conventions
- Clarify the boundary between rhiza (template) and rhiza-tools (CLI) (#761)
- Fix rhiza-tools → rhiza-cli naming in README and GLOSSARY (#766)
- *(adr)* Backfill ADR-0002 through ADR-0009 (#769)
- Add ADR dropdown menu to mkdocs navigation (#771)
- Clarify tests/ as downstream blueprints, not Rhiza's own test suite (#774)
- Flesh out index.md and restructure mkdocs nav with dropdown sections (#776)
- Update ROADMAP.md to reflect v0.8.1-rc.2 and completed work (#781)

### Dependencies
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.4 (#732)
- *(deps)* Update dependency astral-sh/uv to v0.10.4 (#731)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.2 (#739)
- *(deps)* Update github/codeql-action action to v4.32.4 (#738)
- *(deps)* Lock file maintenance (#784)

### Maintenance
- Simplify pytest HTML title hooks across test suites

### Other Changes
- Configure Renovate to auto-rebase when behind base branch (#728)
- Add sync-experimental target to rhiza.mk (#730)
- Remove dry-run mode from shell scripts (#700)
- Fix SBOM missing primary component for NTIA compliance (#734)
- Update marimushka version requirement to 0.3.3 (#735)
- Include benchmark results in the compiled book (#741)
- Add `+RHIZA_SKIP` flag to exclude individual README code blocks from readme tests (#745)
- Add official Rhiza logo to MkDocs documentation site (#749)
- Surface template bundles as the primary abstraction for template selection (#753)
- Add stress test suite with make target and book integration (#676)
- Add `coverage-badge` make target to `test.mk` (#737)
- Add SECURITY.md, secret scanning config, and update template bundles (#757)
- Add Architecture Decision Record (ADR) system with AI-powered automation (#212)
- Remove .rhiza/scripts and all references (#751)
- Update bumpversion configuration for template bundles (#762)
- Add no-op docs targets to book.mk for build resilience (#764)
- Fix formatting of version in template-bundles.yml (#767)
- Delete REPOSITORY_ANALYSIS.md (#772)
- Bump version 0.8.1-rc.2 → 0.8.2

## [0.8.1-rc.2] - 2026-02-17

### Dependencies
- *(deps)* Lock file maintenance (#703)
- *(deps)* Update dependency astral-sh/uv to v0.10.3 (#720)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.36.2 (#722)
- *(deps)* Update actions/checkout action to v6 (#723)
- *(deps)* Update actions/download-artifact action to v7 (#724)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.3 (#721)

### Other Changes
- Renovate should be a bundle (#704)
- Security tests (#692)
- Complete GH_AW_INTEGRATION.md audit trail with Phase 6 commit reference (#711) (#712)
- Add maintainability infrastructure: roadmap, debt tracking, and changelog automation (#698)
- Add stress test suite for Rhiza's Makefile and Git operations (#680)
- Update .claude docs to reflect perfect 10/10 quality score achievement
- Update Phase 1 Quick Wins status in .claude/plan.md
- Add renovate_rhiza_sync.yml to template bundles configuration (#725)
- Bump version 0.8.1-rc.1 → 0.8.1-rc.2

## [0.8.0] - 2026-02-15

### Dependencies
- *(deps)* Update pre-commit hook rhysd/actionlint to v1.7.11 (#674)

### Maintenance
- Update Renovate schedule to run nightly (#683)

### Other Changes
- Add copilot-setup-steps.yml and hooks to template-bundles (#664)
- Update pre-commit config to include unsafe arg (#665)
- Display venv activation instructions after make install (#667)
- Make invocations clearer (#668)
- Ignore mypy_cache (#669)
- Improve release flow, introduce publish fasttrack (#672)
- Enable security and simplicity linting, refactor per-file exceptions (#678)
- Enable tagging in .cfg.toml configuration
- Update quality assessments to reflect recent improvements
- Revise shell scripts assessment after verification
- Remove shell script comment weakness from Documentation section
- Fix Renovate schedule syntax validation error (#688)
- Document dependency version rationale (#687)
- Replace mypy with ty type checker (#671)
- Document VSCode extensions configured in devcontainer (#690)
- Fix score mismatches between summary and detailed sections (#684)
- Add architecture documentation: Mermaid diagrams, naming conventions, and quick reference index (#694)
- Update .claude documentation to reflect recent improvements
- Add developer onboarding (#696)
- Update .claude documentation for Developer Experience improvements
- Releasing
- Hotfix release (#701)
- Fix-bump (#702)
- Bump version 0.7.5 → 0.8.0

## [0.7.5] - 2026-02-14

### Other Changes
- Update renovate.json
- Add workflow to sync rhiza template files (#662)
- Fix formatting in renovate.json (#663)
- Bump version 0.7.4 → 0.7.5

## [0.7.4] - 2026-02-14

### Other Changes
- Enable automatic version tracking for template.yml via Renovate (#658)
- Add test to validate template-bundles.yml file references (#601)
- Bump version 0.7.3 → 0.7.4

## [0.7.3] - 2026-02-14

### Other Changes
- Cyclonedx bom (#661)
- Bump version 0.7.2 → 0.7.3

## [0.7.2] - 2026-02-14

### Documentation
- Consolidate infrastructure docs into .rhiza/docs/ (#638)

### Dependencies
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.2.1 (#606)
- *(deps)* Update dependency astral-sh/uv to v0.10.1 (#607)
- *(deps)* Lock file maintenance (#608)
- *(deps)* Update dependency astral-sh/uv to v0.10.2 (#620)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.2 (#621)
- *(deps)* Update actions/cache action to v5 (#625)
- *(deps)* Update dependency astral-sh/uv to v0.10.2 (#624)
- *(deps)* Update actions/upload-artifact action to v4.6.2 (#648)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.1 (#649)
- *(deps)* Update aquasecurity/trivy-action action to v0.34.0 (#650)
- *(deps)* Update actions/attest-sbom action to v3 (#651)
- *(deps)* Update github/codeql-action action (#653)
- *(deps)* Lock file maintenance (#654)
- *(deps)* Update github artifact actions (major) (#652)

### Maintenance
- Move user customizations from .rhiza/make.d to root Makefile (#589)
- Make tests more DRY (#610)

### Other Changes
- Sync template-bundles.yml version to 0.7.1
- Remove unsupported CLAUDE_INSTALL_DIR environment variable (#587)
- Bundle rhiza tests into rhiza workflows (#590)
- Remove local version_matrix.py - migrate to rhiza-tools (#594)
- Add LFS template bundle with comprehensive test suite (#574)
- Keep a testing placeholder (#595)
- We should not break for no test folder (#597)
- Refactor make.d file references in template-bundles.yml (#598)
- Add missing mk links to template bundles (#602)
- Skip LFS tests when lfs.mk is not present (#604)
- Migrate benchmarks (#588)
- Make lfs tests less rigid (#609)
- Modify bandit command to include config file (#605)
- Delete docs/BENCHMARK.md (#614)
- Create .gitkeep (#615)
- Cache pre-commit environments in CI (#622)
- Add LFS support to GitHub Actions workflow (#619)
- Fix bump target to locate pre-commit when venv not activated (#623)
- Add technical analysis and quality scoring documents (#375)
- Add SBOM generation to release workflow (#628)
- Add Trivy vulnerability scanning to Docker production workflow (#630)
- Add property-based and load/stress testing infrastructure (#632)
- Fix pip security vulnerability CVE-2025-8869 in Docker image
- Consolidate consecutive RUN instructions in Dockerfile
- Upgrade pip to 26.0 to fix CVE-2026-1703
- Replace rhiza-specific benchmarks with placeholder examples (#642)
- Suppress uv environment path mismatch warnings (#645)
- Add `make all` target for local CI validation (#647)
- Add Copilot agent setup steps and session hooks (#643)
- Set default AI model to claude-sonnet-4.5 (#659)
- Update rhiza-hooks to version 0.3.0 (#660)
- Update rhiza to version 0.11.0
- Bump version 0.7.1 → 0.7.2

## [0.7.1] - 2026-02-07

### Dependencies
- *(deps)* Update dependency astral-sh/uv to v0.10.0 (#556)
- *(deps)* Update github/codeql-action action to v4.32.2 (#554)
- *(deps)* Update astral-sh/setup-uv action to v7.3.0 (#555)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.10.0 (#557)
- *(deps)* Lock file maintenance (#581)

### Maintenance
- Migrate and reorganize test suite to .rhiza/tests with categorical structure (#542)
- Add `.rhiza/template-bundles.yml` to define reusable template … (#545)

### Other Changes
- Update .pre-commit-config.yaml (#536)
- Move PRESENTATION and SECURITY (#538)
- Add missing newline to `.rhiza/requirements/tools.txt`
- Revisit tests (#535)
- Cosmetics in pre-commit-config file
- Yaml (#544)
- Add legal and community files section to template (#546)
- Include DevContainer configuration in template-bundles.yml (#547)
- Add benchmarks and Docker sections to template-bundles (#548)
- Update template-bundles.yml (#549)
- Add GitLab CI/CD configuration to template bundles (#550)
- Add `tests` and `marimo` sections to `template-bundles.yml` (#551) (#551)
- Add version field to template-bundles.yml with auto-sync on bump (#553)
- [WIP] Add language identifier to fenced code block in documentation (#559)
- Update CUSTOMIZATION.md with configuration variables (#560)
- Fix installation command for private library (#561)
- Clean up commented includes in rhiza.mk (#562)
- Update release workflow file reference in RELEASING.md
- Clean up template-bundles.yml by removing comments (#565)
- Replace tomli with stdlib tomllib (#564)
- Fix ambiguous directory reference in ASSETS.md (#568)
- Fix composite action token handling via environment variable (#570)
- Revise token scopes section in PRIVATE_PACKAGES.md
- Remove comment about uv version in pre-commit config (#572)
- Update README with token usage details (#571)
- Fix misleading comment referencing non-existent 09-mkdocs.mk (#576)
- Add default value for PDOC_TEMPLATE_DIR (#578)
- Correct test_root_contains_expected_directories structure validation (#580)
- Comment out bumpversion configuration for template-bundles (#584)
- Skip book-related tests when 02-book.mk is missing (#583)
- Remove __init__.py from test directories (#586)
- Bump version 0.7.0 → 0.7.1

## [0.7.0] - 2026-02-05

### Dependencies
- *(deps)* Update dependency astral-sh/uv to v0.9.29 (#508)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.29 (#509)
- *(deps)* Update pre-commit hook abravalheri/validate-pyproject to v0.25 (#511)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.9.29 (#510)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.15.0 (#512)
- *(deps)* Update dependency astral-sh/uv to v0.9.30 (#524)
- *(deps)* Update pre-commit hook astral-sh/uv-pre-commit to v0.9.30 (#526)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.30 (#525)
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.1.4 (#527)

### Other Changes
- Enable private GitHub package dependencies in template workflows (#498)
- Update GitHub workflows to configure git for private repos using GH_P… (#504)
- Fix syntax error in git auth configuration
- Fix bump (#502)
- Configure git auth for private packages (#505)
- Keeping env insync (#503)
- Remove mutmut workflow from test makefile (#506)
- Make GitHub token input optional (#507)
- Update logo path in README.md
- Separate docs target into dedicated docs.mk file (#514)
- Add MkDocs integration to companion book (#523)

## [0.6.2] - 2026-02-02

### Bug Fixes
- Fix make overrides (#417)

### Dependencies
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.36.1 (#425)
- *(deps)* Update dependency astral-sh/uv to v0.9.27 (#423)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.27 (#424)
- *(deps)* Update astral-sh/setup-uv action to v7.2.1 (#460)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.28 (#462)
- *(deps)* Update actions/setup-python action to v6.2.0 (#463)
- *(deps)* Update docker/login-action action to v3.7.0 (#464)
- *(deps)* Update github/codeql-action action to v4.32.0 (#465)
- *(deps)* Update dependency astral-sh/uv to v0.9.28 (#461)
- *(deps)* Update peter-evans/create-pull-request action to v8.1.0 (#466)
- *(deps)* Update python docker tag to v3.14 (#481)
- *(deps)* Update docker docker tag to v29 (#482)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.28 (#480)
- *(deps)* Lock file maintenance (#485)
- *(deps)* Update pre-commit hook jebel-quant/rhiza-hooks to v0.1.3 (#490)
- *(deps)* Update github/codeql-action action to v4.32.1 (#499)

### Other Changes
- Smallfix (#420)
- Ensure rhiza workflows are uppercase (#419)
- Fix test_book.py failures when book folder is absent (#422)
- Pin GitHub Actions to full SemVer versions (#348)
- [WIP] Fix ImportError in test_rhiza_workflows.py (#427)
- Skip SLSA attestation for private repositories (#429)
- Enable Git LFS support in GitHub Actions workflow (#445)
- Fix mypy invocation to use `uv run` instead of `uvx` (#447)
- Delete src directory (#448)
- Docscoverage (#449)
- Add type checking step to Rhiza security workflow (#450)
- Update mypy target dependency in rhiza.mk (#451)
- Update test_docstrings.py (#452)
- Install git-lfs in CI before script (#455)
- Add type checking step to Rhiza security workflow (#457)
- Remove git lfs install from CI workflow (#458)
- Update rhiza_mypy.yml
- Update deptry image version in workflow (#467)
- Update rhiza_validate.yml (#469)
- Update rhiza_deptry.yml (#468)
- Update container image for security scanning workflow (#470)
- Update base image from trixie-slim to bookworm-slim (#471)
- Add gitlab Renovate workflow for automated dependency updates
- Update Docker image version in rhiza_validate.yml (#472)
- Update Docker image version in workflow (#474)
- Update Docker image version in rhiza_sync.yml (#473)
- Update pre-commit image version to 0.9.28 (#475)
- Enable Renovate management for GitLab CI workflows (#477)
- Fix invalid GitLab CI manager name in Renovate config (#479)
- Gitlab (#459)
- Remove devcontainer publishing from GitLab CI/CD (#484)
- Move to rhizahooks (#488)
- Housekeeping (#487)
- Move bandit config to pyproject.toml (#414)
- Refactor doctest discovery to use src_path (#489)
- Tschm docstrings (#492)
- Bump version 0.6.1 → 0.6.2

## [0.6.1] - 2026-01-26

### Bug Fixes
- Incorrect values (#333)

### Dependencies
- *(deps)* Update pre-commit hook pycqa/bandit to v1.9.2 (#339)
- *(deps)* Lock file maintenance (#378)
- *(deps)* Update pre-commit hook pycqa/bandit to v1.9.3 (#380)
- *(deps)* Update actions/attest-build-provenance action to v3 (#381)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.14 (#394)
- *(deps)* Lock file maintenance (#396)
- *(deps)* Update dependency pandas to v3 (#395)
- *(deps)* Lock file maintenance (#397)
- *(deps)* Lock file maintenance (#398)
- *(deps)* Lock file maintenance (#413)

### Maintenance
- Chore(deps-dev)(deps-dev): bump marimo in the python-dependencies group (#334)

### Other Changes
- Add hypothesis dependency to tests requirements (#322)
- Add bandit security linter to pre-commit hooks (#329)
- Add docs-coverage target using interrogate (#331)
- Add B, C4, SIM, PT, RUF, S, ERA, T10, TRY, ICN, PIE, PL rule sets to ruff.toml (#327)
- Create rhiza_security.yml (#324)
- Add performance benchmarks workflow (#323)
- Add mypy hook for type checking in pre-commit (#325)
- Group prs dependabot (#332)
- Remove mypy hook from .pre-commit-config.yaml (#337)
- Ensure workflow names for rhiza start with rhiza (#335)
- Remove private condition (#340)
- Improve ruff.toml readability with one rule per row (#346)
- Revisit rhiza notebook (#347)
- Add comprehensive repository quality analysis (#352)
- Add comprehensive glossary of Rhiza-specific terms (#356)
- Add SECURITY.md with vulnerability reporting process (#354)
- Add quick reference card for common Rhiza operations (#358)
- Tighten dev dependency version constraints (#355)
- Document purpose of each dev dependency (#357)
- Update analysis.md: score improved 8.8 → 9.4
- Add architecture diagrams with mermaid (#359)
- Add demo recording instructions and scripts (#360)
- Update analysis.md: score improved 9.4 → 9.5
- Remove unnecessary mo parameter from app cells in rhiza.py (#362)
- Add unit tests for version_matrix.py and check_workflow_names.py
- Fmt
- Add custom exceptions and tests for version_matrix.py (#349)
- Harden release.sh with dry-run flag and shellcheck fixes (#350)
- Add simple "Hello, World!" script in `hello` module
- Hello (#365)
- Update analysis.md: score improved 9.5 → 9.6
- Update analysis.md: Dependency Management 9 → 10
- Update analysis.md: Shell Scripts 9 → 10
- Add benchmark regression detection to CI
- Update analysis.md: Test Coverage 9→10, CI/CD 9→10
- Simplify benchmark workflow paths and remove redundant install step in CI
- Add conditional check for benchmarks.json in benchmark workflow
- Enable full shellcheck validation in actionlint (#361)
- Propagate UV_EXTRA_INDEX_URL to workflows invoking make install (#370)
- Mypy (#367)
- Add mypy CI workflow and update analysis to 10/10
- Update ruff.toml (#374)
- Set UV_EXTRA_INDEX_URL in CI workflow (#376)
- Add SLSA provenance attestations to release workflow (#353)
- Deactivate rhiza_mypy for now (#379)
- Apply coverage threshold only when SOURCE_FOLDER exists (#383)
- Update-global-git-url for orgs (#384)
- Extend asserts in test_notebooks.py to cover marimo sandbox setup error (#387)
- Simplify pdocs build for logo (#390)
- Allow configurable code coverage (#388)
- Specify Python version for deptry, mypy and fmt commands (#385)
- Use rhiza pr summarise (#366)
- Ensure pr-description doesn't get committed (#392)
- Make marimo run cwd consitent in make and tests (#391)
- Add io.shields coverage badge JSON generation to book target (#400)
- Delete book/marimo/notebooks/dummy.py
- Fix `make book` failure when marimo folder absent (#402)
- 405 what if there is no book folder (#406)
- Simplify release (#418)
- Bump version 0.6.0 → 0.6.1

## [0.6.0] - 2026-01-16

### Bug Fixes
- Copilot install (#262)
- Fix make customisations (#261)

### Dependencies
- *(deps)* Lock file maintenance (#231)
- *(deps)* Update dependency astral-sh/uv to v0.9.22 (#241)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.22 (#242)
- *(deps)* Update dependency astral-sh/uv to v0.9.24 (#254)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.24 (#255)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.11 (#256)
- *(deps)* Lock file maintenance (#288)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.26 (#319)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.13 (#320)
- *(deps)* Update dependency astral-sh/uv to v0.9.26 (#318)

### Maintenance
- Chore(deps-dev)(deps-dev): bump plotly from 6.5.1 to 6.5.2 (#314)

### Other Changes
- Vmove customisations to allow better customisability (#223)
- If repo is rhiza-* then this wouldn't work (#230)
- Makefile agentics and improvements (#229)
- Update Makefile.agentic
- Update Makefile.agentic (#233)
- Update renovate.json (#235)
- Update documentation (#238)
- Remove GITLAB_CI.md from root level (#240)
- Ensure commit on bump and update lock (#245)
- Add headline/slogan (#246)
- Create dedicated rhiza makefile (#248)
- Add tests for validating bash examples in README.md (#249)
- Remove redundant install-dev-deps.sh script (#258)
- Update pre-commit workflow to use `make fmt` and adjust Makefile to a… (#259)
- Configure deptry package-to-module name mappings (#264)
- Move RHIZA_LOGO and print-logo from central Makefile to Makefile.rhiza (#266)
- Fix Workflow Configuration section: document .python-version, clarify PAT_TOKEN, fix template path, remove obsolete variables (#268)
- Clean up (#280)
- Add GitLab CI/CD section to README with pointer to .gitlab/README.md (#275)
- Add presentation section to README.md (#277)
- Consolidate documentation customization content in book/README.md (#279)
- Consolidate devcontainer documentation into .devcontainer/README.md (#273)
- Add typer dependency to tools.txt
- Update github tools in devcontainer (#287)
- Add docker make & align python versions
- Default version to avoid warning (#289)
- Replace generate-coverage-badge.sh with Python utility using typer (#284)
- Remove marimushka.sh shell script and inline logic into Makefile (#282)
- Replace update-readme-help.sh with uvx rhiza-tools command (#291)
- Replace local generate_coverage_badge.py with rhiza-tools command (#293)
- Remove broken update-readme & force rhiza-tools 0.2.0 (#294)
- Add Makefile tab indentation rules to .editorconfig (#299)
- More power to the makefile (#296)
- Introducing marimo.mk
- Update marimushka tests and Makefile logic (#303)
- Convergence make and ci/cd (#297)
- Move agentic make (#304)
- User overrides included in .rhiza/rhiza.mk (#309)
- Simplify README.md flow and structure (794 → 470 lines) (#308)
- Use UK english instead of US english (#311)
- Use uv package ecosystem (#313)
- Add _benchmarks to .gitignore (#317)
- Rename and align workflow display names (github) (#316)
- Bump version 0.5.0 → 0.6.0

## [0.5.0] - 2026-01-03

### Other Changes
- 199 revisit deptry (#200)
- Establish .rhiza/requirements folder for dev dependencies (#204)
- 215 move to dependency groups (#216)
- Add pytest-mock and benchmark dependencies
- 215 move to dependency groups (#217)
- Move to rhiza-tools for bump (#218)
- Update version requirement for rhiza tools (#220)

## [0.4.1] - 2026-01-01

### Bug Fixes
- Fix broken deptry test (#161)

### Dependencies
- *(deps)* Lock file maintenance (#164)
- *(deps)* Update dependency astral-sh/uv to v0.9.21 (#174)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.21 (#175)
- *(deps)* Update pre-commit hook rhysd/actionlint to v1.7.10 (#176)

### Other Changes
- Delete SECURITY.md
- Reduce the action (#150)
- Remove redundant tests for install target logic and update expected paths and script descriptions in tests
- No action (#153)
- Add GitLab CI/CD workflows with feature parity to GitHub Actions (#155)
- Add Marimo job template for testing notebooks in gitlab wing
- Refactor Marimo CI workflow for gitlab better clarity
- Remove devcontainer gitlab (#160)
- Refactor clean target in Makefile
- Update deptry command to check for 'src' directory
- Create rhiza_codeql.yml (#163)
- Update rhiza_codeql.yml
- Fix duplicate workflow runs on PR branches (#173)
- 169 marimo notebooks not erroring at build stage in the event of failure (#172)
- Several README.md files updated for GitHub (#165)
- Cleanup badges (#178)
- Add CodeFactor badge to README (#182)
- Fix all Bandit S607 security warnings by using absolute paths for executables in tests (#184)
- Add python-dotenv dependency for tests (#180)
- Fix subprocess call using partial executable path in test_release_script.py (#186)
- Fix SC2181: check exit code directly in bump.sh (#188)
- Coverage number (#191)
- Skip validate/sync targets in rhiza repository (#193)
- Revisit gitlab workflows (#166)
- Remove src folder (#196)
- Remove coverage badge from README
- 167 dealing with env files (#197)

## [0.4.0] - 2025-12-26

### Other Changes
- Fix typo in README.md (#140)
- Update TOKEN_SETUP.md path in rhiza_sync.yml (#141)
- Update README with new test script descriptions (#143)
- Moving dependabot and renovate (#149)
- Establish .rhiza folder for platform-agnostic CI/CD infrastructure (#145)

## [0.3.2] - 2025-12-25

### Other Changes
- Ensure correct rhiza version for sync (#130)
- Add validate to the makefile interface (will fail for templates) (#131)
- Move .github/actions to .github/rhiza/actions folder (#129)
- Reorganize GitHub configuration under .github/rhiza namespace (#133)
- Move workflow files to .github/workflows/ with rhiza_ prefix (#135)
- Improve make install (#137)
- ,gitignore also ignoring .DS_Store files?

## [0.3.1] - 2025-12-24

### Bug Fixes
- *(deps)* Update dependency pre-commit to v4.5.1 (#67)

### Dependencies
- *(deps)* Update dependency astral-sh/uv to v0.9.18 (#63)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.18 (#64)
- *(deps)* Update jebel-quant/sync_template action to v0.4.3 (#65)
- *(deps)* Lock file maintenance (#66)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.10 (#73)
- *(deps)* Lock file maintenance (#90)

### Maintenance
- Test the structure and files with rhiza (#68)

### Other Changes
- Improve API docs (#55)
- Fix version (#56)
- Add 'Private :: Do Not Upload' classifier
- 57 remove the copier support (#58)
- Add MakefileTools extension to devcontainer (#61)
- Update sync target to install-uv and change command
- Sync without sync_template but with rhiza
- Rhiza without the attempted branch deletion
- Add CONFIG.md to GitHub directory (#71)
- Force materialization in sync target
- Remove sync.sh existence check from tests
- Merge pull request #72 from Jebel-Quant/tschm-patch-1
- Don't build the package if [build-system] is missing (#60)
- Repo naming detail (#77)
- Fix pdoc import failure when package metadata unavailable (#76)
- Add comprehensive repository analysis with 9.0/10 rating (#79)
- Add inline comments explaining complex logic in scripts (#81)
- Presentation (#87)
- Add PRESENTATION.md with Marp slides introducing the repository (#89)
- Fix Marp server mode to accept directory instead of file (#92)
- Filter workflow badges to main branch only (#101)
- Update badge links in README.md (#104)
- Add workflow (#86)
- Fix sync workflow PR creation on scheduled runs (#105)
- Add Dependabot configuration for automated dependency updates (#98)
- Update security.yml (#112)
- Split Makefile into modular components by functional area (#107)
- New sync (#110)
- Delete .github/template.yml
- Do not use a Marimo folder in the template (too much hassle to avoid overwriting it)
- Prevent validation job in rhiza repository
- Add benchmark target to Makefile.tests (#114)
- Refactor sync workflow by removing unnecessary steps (#113)
- Ignore benchmark folder by default when running make test (#117)
- Add fallback targets for book-related Make commands when book/ folder is missing (#116)
- Move benchmark init and update GitHub folder structure (#118)
- Folder structure (#122)
- Add README.md to presentation folder with Marp usage documentation (#121)
- Remove inaccurate MAKEFILE_GUIDE.md
- Disable Docker dependency updates
- Add comprehensive Marimo showcase notebook (#127)
- Delete .github/workflows/security.yml

## [0.3.0] - 2025-12-16

### Other Changes
- Remove startup.sh (#40)
- Run in headless with no token (#42)
- More-tests (#43)
- 44 remove src and dedicated test cli commands test (#45)
- Jazzup landing page (#46)

## [0.2.0] - 2025-12-16

### Other Changes
- Materialize (#38)

## [0.1.0] - 2025-12-16

### Dependencies
- *(deps)* Lock file maintenance (#37)

### Other Changes
- Add inject_rhiza.sh for automated repository integration (#31)

## [0.0.3] - 2025-12-16

### Other Changes
- Remove 'Private :: Do Not Upload' classifier
- 33 remove the addpy nonsense (#34)

## [0.0.2] - 2025-12-16

### Other Changes
- Hello script. Try with uv run hello
- Fmt

## [0.0.1] - 2025-12-16

### Bug Fixes
- Fixtures in test_env
- Fix the action?
- Fix action?
- Fixing test_env
- Fixing broken test if no pyproject file
- Fixing linting problem
- Fixing export of notebooks to html
- *(deps)* Update dependency marimo to v0.17.8 (#137)
- *(deps)* Update dependency pytest to v9 (#140)
- *(deps)* Update dependency pre-commit to v4.5.0 (#150)
- *(deps)* Update dependency marimo to v0.18.0 (#149)
- Fixing the tests if not executed from the project_root folder
- Fix forgotten \
- *(deps)* Update dependency marimo to v0.18.1 (#169)
- Fix test_release_script? (#211)
- *(deps)* Update dependency marimo to v0.18.2 (#225)
- Fix when tag can't be signed (#240)
- *(deps)* Update dependency marimo to v0.18.3 (#252)
- *(deps)* Update dependency pytest to v9.0.2 (#260)
- *(deps)* Update dependency marimo to v0.18.4 (#297)

### Dependencies
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.4
- *(deps)* Update tschm/cradle action to v0.3.02 (#4)
- *(deps)* Update dependency python to 3.13
- *(deps)* Update tschm/cradle action to v0.3.04
- *(deps)* Update peter-evans/create-pull-request action to v7
- *(deps)* Update tschm/.config-templates action to v0.1.6 (#8)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.5
- *(deps)* Update tschm/cradle action to v0.3.05
- *(deps)* Update tschm/.config-templates action to v0.1.7 (#12)
- *(deps)* Update tschm/cradle action to v0.3.06 (#13)
- *(deps)* Update tschm/.config-templates action to v0.1.8
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.7
- *(deps)* Update pre-commit hook crate-ci/typos to v1.35.1 (#16)
- *(deps)* Update actions/download-artifact action to v5
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.8 (#25)
- *(deps)* Update tschm/.config-templates action to v0.3.4 (#17)
- *(deps)* Update pre-commit hook pre-commit/pre-commit-hooks to v6
- *(deps)* Update tschm/.config-templates action to v0.4.6
- *(deps)* Update actions/checkout action to v5
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.9
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.33.3 (#50)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.10
- *(deps)* Update actions/upload-pages-artifact action to v4
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.11 (#58)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.12.12
- *(deps)* Update softprops/action-gh-release action to v2.3.3 (#60)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.13.0
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.13.1 (#70)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.34.0 (#71)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.13.2 (#85)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.13.3 (#89)
- *(deps)* Update softprops/action-gh-release action to v2.4.0 (#90)
- *(deps)* Update astral-sh/setup-uv action to v7 (#92)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.0 (#91)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.34.1 (#94)
- *(deps)* Update softprops/action-gh-release action to v2.4.1 (#97)
- *(deps)* Update pre-commit hook rhysd/actionlint to v1.7.8 (#95)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.1 (#99)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.4 (#102)
- *(deps)* Update actions/setup-python action to v6 (#104)
- *(deps)* Update dependency python to 3.14 (#111)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.5 (#110)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.2 (#114)
- *(deps)* Update github artifact actions (#118)
- *(deps)* Update mcr.microsoft.com/devcontainers/python docker tag to v3.14 (#112)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.6 (#119)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.3 (#122)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.7 (#121)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.4 (#125)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.8 (#126)
- *(deps)* Update softprops/action-gh-release action to v2.4.2 (#127)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.35.0 (#128)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.9 (#129)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.5 (#130)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.10 (#136)
- *(deps)* Update pre-commit hook igorshubovych/markdownlint-cli to v0.46.0 (#139)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.10 (#141)
- *(deps)* Update hadolint/hadolint-action action to v3.3.0 (#138)
- *(deps)* Update python docker tag to v3.14 (#142)
- *(deps)* Lock file maintenance (#143)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.11 (#146)
- *(deps)* Update pre-commit hook rhysd/actionlint to v1.7.9 (#148)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.6 (#147)
- *(deps)* Update actions/checkout action to v6 (#151)
- *(deps)* Lock file maintenance (#152)
- *(deps)* Lock file maintenance (#170)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.13 (#168)
- *(deps)* Update dependency python to 3.14
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.7 (#179)
- *(deps)* Update actions/checkout action to v6 (#181)
- *(deps)* Update actions/setup-python action to v6 (#182)
- *(deps)* Lock file maintenance (#183)
- *(deps)* Update softprops/action-gh-release action to v2.5.0 (#199)
- *(deps)* Lock file maintenance (#200)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.14 (#201)
- *(deps)* Lock file maintenance (#202)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.15 (#213)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.8 (#237)
- *(deps)* Lock file maintenance (#253)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.16 (#259)
- *(deps)* Lock file maintenance (#275)
- *(deps)* Update ghcr.io/astral-sh/uv docker tag to v0.9.17 (#296)
- *(deps)* Lock file maintenance (#298)
- *(deps)* Update pre-commit hook igorshubovych/markdownlint-cli to v0.47.0 (#305)
- *(deps)* Update pre-commit hook astral-sh/ruff-pre-commit to v0.14.9 (#306)
- *(deps)* Lock file maintenance (#307)
- *(deps)* Update github artifact actions (#316)
- *(deps)* Update pre-commit hook python-jsonschema/check-jsonschema to v0.36.0 (#29)

### Maintenance
- Test env again
- Build step
- Build only if there is a pyproject file
- Testing notebooks
- Testing notebooks
- Build the book with make book
- Test the Makefile
- Test taskfile
- Tests and linting
- Test_taskfile.py make sure stdout and stderr are str
- Ci with setup-project action
- Refactor some workflows
- Refactor some workflows
- Refactor some workflows
- Build explicitly without the deps construct
- Testing README (#144)
- Test
- Testing notebooks (#6)

### Other Changes
- Initial commit
- Update .gitignore
- Remove README
- Generic ci.yml
- Generic ci.yml
- Generic pre-commit
- Generic pre-commit
- Renovate
- Renovate
- Release job
- Update .gitignore
- Deptry and devcontainer
- Deptry and devcontainer
- CODE of CONDUCT and CONTRIBUTING
- Makefile
- Makefile with docs
- Editorconfig
- Update CONTRIBUTING.md
- Update CONTRIBUTING.md
- Update pre-commit.yml
- Editorconfig
- Update CONTRIBUTING.md
- Editorconfig
- Update file
- Update file
- Ruff.toml
- Update test_env.py
- Release
- Release
- Ruff more details
- Robuster Makefile
- Ruff more details
- Unsafe fixes
- Pydocstyle
- Merge pull request #2 from tschm/renovate/astral-sh-ruff-pre-commit-0.x
- Clear uv
- Manual tag
- Manual tag
- Manual tag
- Release job
- Release job
- Release job
- Update release.yml
- Update release.yml
- Runner for gh-release
- Gh release without artifacts
- Comments
- Potential fix for code scanning alert no. 1: Workflow does not contain permissions
- Merge pull request #3 from tschm/alert-autofix-1
- Merge pull request #5 from tschm/renovate/python-3.x
- Update workflow
- Towards a workflow
- Updater workflow
- Update with commit
- Remove update
- Update
- Update script
- Merge pull request #6 from tschm/renovate/tschm-cradle-0.x
- Update script
- Rename to up.sh
- Up script
- Up script
- Remove update
- No need to remove the script in the sync workflow
- Script
- Dedicated action
- Sync workflow
- Update
- Towards using the PAT token
- Update sync.yml
- Dealing with token gymnastics
- Update sync.yml
- Merge pull request #7 from tschm/renovate/peter-evans-create-pull-request-7.x
- Fmt
- Workflow dispatch for sync job
- Enhance Makefile and include generic test_docs
- Update sync.yml
- Addressing some tests
- Header in most files
- No hyperlinks in md
- Pre-commit-config
- Merge pull request #10 from tschm/renovate/astral-sh-ruff-pre-commit-0.x
- Merge pull request #11 from tschm/renovate/tschm-cradle-0.x
- Update book.yml
- Execute book only if pushed to main or master
- Revisited Contributing guide
- Deptry job
- Update Makefile
- Merge pull request #15 from tschm/renovate/tschm-.config-templates-0.x
- Merge pull request #14 from tschm/renovate/astral-sh-ruff-pre-commit-0.x
- Encoding of README
- Find the project root
- Refactor workflows and Makefile for consistent `pyproject.toml` checks and improved clarity
- Remove typo pre-commit action
- Upload everything as there is not pyproject.toml
- Handle missing `dist/` directory during upload in release workflow
- Handle missing `dist/` directory during upload in release workflow
- Update release.yml
- Handle missing `dist/` directory during upload in release workflow
- Handle missing `dist/` directory during upload in release workflow
- Update sync
- Update .gitignore
- Problem in release
- Problem in release
- Problem in release
- Problem in release
- Devcontainer revisited
- Update sync.yml
- Merge pull request #18 from tschm/renovate/major-github-artifact-actions
- Robuster Makefile
- With make lint and make fmt
- Deptry with makefile
- Deptry
- Potential fix for code scanning alert no. 4: Workflow does not contain permissions
- Merge pull request #19 from tschm/making
- Make docs and make test
- Merge pull request #21 from tschm/making
- Use make build
- CI pointing to tests
- Remove the juggling of the .env file
- Sync with a modern version
- Merge pull request #22 from tschm/make-release
- Updated Makefile
- Updated Makefile
- Updated Makefile
- Updated Makefile
- Updated Makefile
- Updated Makefile
- Merge pull request #23 from tschm/newMakefile
- Merge pull request #24 from tschm/make-release
- Updated Makefile
- Updated Makefile
- Updated Makefile
- Remove src folder
- Use code of conduct from chebpy and corrections in ruff.toml and execute book only when on pushing on main
- Fmt
- Fixing Makefile
- Taskfiles
- Phasing out the Makefile
- Phasing out the Makefile
- Use task instead of make
- Use task instead of make
- Use task instead of make
- Use task instead of make
- Use task instead of make
- Use task instead of make
- Fmt
- Use task instead of make
- Use task instead of make
- Add uv/uvx to path
- Use task instead of make
- Install uv/uvx
- Quality tasks
- Deptry workflow
- Quality taskfile
- Deptry workflow only if there is a pyproject file
- Update of workflows
- Updated taskfile without test file
- Updated taskfile without test file
- Updated taskfile without test file
- Installing task and uv in marimo.yml
- Update sync.yml
- Setting missing permissions
- Update sync.yml
- Merge pull request #26 from tschm/renovate/pre-commit-pre-commit-hooks-6.x
- Moving taskfiles
- Don't create README
- Updated test_taskfile
- Update Taskfile.yml
- Don't create README
- Bring back a small Makefile
- Release job was missing task setup
- Install task
- Run tests now?
- Run tests now?
- Run tests now?
- Run tests now?
- Run tests now?
- More testing
- Update action.yml
- Merge pull request #27 from tschm/renovate/tschm-.config-templates-0.x
- README
- README
- Update ci.yml
- Sync
- Merge pull request #28 from tschm/renovate/actions-checkout-5.x
- Ignore .output
- Merge pull request #32 from tschm/30-ignore-outputtxt
- Marimo results only for topfolder
- Merge pull request #33 from tschm/31-in-marimo-loop
- Only top folder for marimushka
- Merge pull request #35 from tschm/34-only-top-folder-for-marimushka-job
- Update .gitignore
- Update cleanup.yml
- Ruff ignored for {{ }}
- Merge pull request #39 from tschm/renovate/astral-sh-ruff-pre-commit-0.x
- Update CONTRIBUTING.md
- Merge pull request #42 from tschm/tschm-patch-2
- Update CODE_OF_CONDUCT.md
- Merge pull request #40 from tschm/tschm-patch-1
- Robuster message check
- Remove the skipped test
- Remove the skipped test
- Merge pull request #44 from tschm/41-robustly-the-test-task-files
- Update marimo.yml
- Merge pull request #43 from tschm/tschm-patch-3
- Update test_taskfile.py
- Merge pull request #46 from tschm/tschm-patch-3
- Update docs.yml
- Update .github/taskfiles/docs.yml
- Merge pull request #45 from tschm/tschm-patch-2
- Remove obsolete empty line
- Robuster cleanup and docs
- Wording in CONTRIBUTING
- Fmt
- 📝 Add docstrings to `cleanup-and-docs`
- Merge pull request #49 from tschm/coderabbitai/docstrings/dff6bf1
- Fmt
- Cleanup bring back the r
- Merge pull request #48 from tschm/cleanup-and-docs
- Remove old code patch
- Remove outdated comment
- Render the project
- Render the project
- Do not use token in action
- Do not use token in action
- Do not reinstall task?
- Merge pull request #52 from tschm/51-introduce-the-render-step
- Update docs.yml
- Cleaning steps
- Cleaning steps
- Update .github/taskfiles/build.yml
- Cleaning steps
- Token?
- Obsolete "and"
- README corrections
- Merge pull request #53 from tschm/cleaning
- Merge pull request #54 from tschm/renovate/astral-sh-ruff-pre-commit-0.x
- Merge pull request #55 from tschm/renovate/actions-upload-pages-artifact-4.x
- Support lfs
- Support lfs
- Merge pull request #56 from tschm/cleaning
- Update config templates action reference
- Merge pull request #57 from markrichardson/patch-1
- Change target Python version from py312 to py311
- Enable LFS support in checkout action
- Merge pull request #59 from tschm/renovate/astral-sh-ruff-pre-commit-0.x
- Lfs support in book
- Merge pull request #61 from tschm/cleaning
- Moving taskfiles out of .github folder
- Renovate file for Gitlab
- Remove the .gitignore file
- Update .editorconfig
- Don't copy Gitlab material
- Ignore .idea folder
- README also for Gitlab
- Fmt issues
- Fmt
- Update .gitlab-ci.yml
- Update .gitlab/ci-templates/sync-config-templates.yml
- Remove files when extracting for Gitlab
- Merge pull request #63 from tschm/towardsGitlab
- Merge pull request #62 from tschm/renovate/astral-sh-ruff-pre-commit-0.x
- Cleaning obsolete stuff
- Fmt
- Merge pull request #64 from tschm/updateTestTaskfile
- Comment out build and info print commands
- Add dependencies to quality tasks in YAML file
- Update taskfiles/quality.yml
- Merge pull request #67 from tschm/tschm-patch-2
- Update build command to use 'uvx' instead of 'uv'
- Merge pull request #66 from tschm/tschm-patch-1
- Include permissions for workflow actions (#69)
- Add error handling to build command
- Add PATH variable to Taskfile.yml
- Remove PATH export in build.yml
- Refactor SOURCE_FOLDER assignment in quality.yml
- Add -s flag for quieter Task operations (#74)
- Improve .devcontainer config (#72)
- More devcontainer config (#75)
- 79 remove gitlab support for now (#80)
- 77 action with explicit devcontainer copy (#78)
- Updated README (#87)
- Update token in sync.yml to use GITHUB_TOKEN
- Update CI and Release badge links in README
- Update README.md
- No longer use the PAT_TOKEN
- Actually PAT_TOKEN needed
- Run book with push to default_branch
- Run book with push to main or master
- Correct outdated comment
- If script header is detected
- Watch out for # /// script
- Skip sync job for self-referential .config-templates repo
- Merge remote-tracking branch 'origin/main'
- Merge remote-tracking branch 'origin/main'
- Install task locally per repo
- Update last updated date in README
- Install uv/uvx also in the same bin folder as task
- Install uv/uvx also in the same bin folder as task
- Install uv/uvx also in the same bin folder as task
- Install uv/uvx also in the same bin folder as task
- Linting corrected
- Tree bin
- Explicit builds in docs
- Install from Makefile
- Explicit path
- Potential fix for code scanning alert no. 7: Workflow does not contain permissions (#93)
- Install explicitly
- Explicit install in setup
- Cosmetics
- Setup using ./bin/uv
- Extend uv sync --all-extras (#96)
- Extend triggers to work on fork PRs
- Improve descriptions
- Be explicit wrt to branches. Format
- Merge pull request #100 from tschm/ci-from-fork
- Revisit linting (#98)
- Fix badge formatting for Python version in README (#105)
- Put ./bin into Path for GitHub (#107)
- Update ruff.toml to ignore specific pydocstyle rules (#108)
- Add conditional requirements installation in CI (#109)
- Robustify some jobs (#113)
- Update ci.yml
- Remove './' from uvx command in deptry.yml (#117)
- Refactor virtual environment setup in build.yml (#115)
- Update Python version badge in README (#120)
- Remove task install from devcontainer (#123)
- Extend pydocstyle selection for docstrings
- Upgrade sync_template to v0.4.1
- Update last updated date in README
- Update startup script for Marimo installation (#124)
- Simple structure check
- Simple structure check
- Simple structure check
- Readme (#132)
- Update README for Python code block formatting
- Merge remote-tracking branch 'origin/main'
- Readme2 (#133)
- Merge remote-tracking branch 'origin/main'
- Revisit comments
- Revisit comments
- Add example (#134)
- Docker (#135)
- Enable the docckerfile manager for renovate
- Update Dockerfile
- Remove Release badge from README
- Change last updated date to November 20, 2025
- Test readme (#145)
- Update test_readme.py
- Fmt
- Added UV_NO_MODIFY_PATH as True to avoid mutating users shell on install (#153)
- Protect main and master  via settings.yml
- Failing test. Can i commit?
- Enforce also for admins
- Commit broken test
- Settings
- Delete tests/test_pseudo.py
- Add initial test for pseudo functionality
- Remove pseudo test
- Do not use automerge as standard in sync.yml (#158)
- Install jq and libatomic1? (#159)
- Don't push to pypi (#161)
- No env (#162)
- Don't push to pypi
- Add abort step for PyPI publish condition
- Remove abort step for PyPI publish
- Refactor .env variable loading in release workflow
- Remove PUBLISH_TO_PYPI abort step from workflow
- Don't push to pypi (#163)
- Update deployment condition for GitHub Pages
- Add 'Private :: Do Not Upload' classifier (#164)
- 165 remove task (#166)
- Extract hardcoded bin paths into Makefile variables (#171)
- Add optional build.sh hook for downstream repos in book workflow (#173)
- Use uppercase for release name (#175)
- Add devcontainer CICD workflow
- Merge branch 'main' into add-devcontainer-workflow
- Add branch filters to push trigger
- Use consistent username for GHCR authentication
- Merge pull request #174 from HarryCampion/add-devcontainer-workflow
- Ensure ci runs if changes to workflows too
- Add good practice comments (#176)
- Potential fix for code scanning alert no. 8: Workflow does not contain permissions (#178)
- Add devcontainer to release cycle and improve release workflow (#177)
- Merge branch 'main' into renovate/python-3.x
- Merge pull request #180 from tschm/renovate/python-3.x
- Merge branch 'tschm:main' into update-workflow-paths
- Packages write required for publish
- Simplify push
- Allow custom feed publishing
- Improve release flow
- Draft releases are allowed
- Improve release logic
- Remove unnecessary publish artifact to release, adds complexity
- Make 'finalise-release' conditions more explicit
- Merge pull request #184 from HarryCampion/update-workflow-paths
- Fix README file references and update include list (#186)
- Misleading comment
- Potential fix for code scanning alert no. 9: Workflow does not contain permissions (#187)
- Update README.md
- Create test_docstrings.py (#197)
- Release auto bumping (#195)
- Fix release script for conflicting tag (#203)
- Add new extensions to devcontainer (#205)
- Reorganize scripts and implement two-step release process (#206)
- Make pdoc great again (#212)
- Add make sync target for manual template synchronization (#217)
- Add backup for sync script and improve directory handling
- Add debugger tools for invoking custom scripts (#222)
- Sign release tags using GPG (-s flag) (#221)
- Add configurable Python version control for workflows (#216)
- Move .dockerignore into docker/ folder  (#218)
- Don't upload the artifacts at all for the GitHub release (#194)
- Update README for releasing and versioning section
- Update README for GitHub actions and workflows (#226)
- Mock gpg (#224)
- Add default Python version to setup action
- 228 address the 313 problem again (#229)
- Fix nested file exclusions in template sync (#231)
- 239 python max version (#241)
- Modify exclude note in customization scripts (#250)
- Use logging across all tests (#251)
- Separate bump and release into distinct scripts (#256)
- Use var for deployment, defaults true and will continue on error if private repo for example fails (#257)
- Add GitHub Codespaces launch badge (#267)
- Add GitHub Codespaces badge to README
- Forgive if there is no pyproject.toml (as for example in the early st… (#249)
- Moving the tests into a separate folder within tests (#262)
- Sync with sync (#264)
- Update README and CONTRIBUTING to reflect interactive release process (#270)
- Logging (#271)
- Read pythoin version as JSON (#273)
- Bring fixtures needed by test_config_templates into test_config... (#279)
- Allow customisations for pdocs (#276)
- Switch to using marimushka for notebook building (#277)
- Add src to path for build of marimushka (#280)
- Fix marimushka (#282)
- Fix typo in pytest.ini comment (#283)
- Remove test scripts from .gitignore (#284)
- Replace assertions with warnings in test_structure for missing files/folders (#286)
- Auto-generate Makefile help output in README (#290)
- Handle missing Makefile help section in update-readme-help.sh (#292)
- Remove gpg signing tests (#295)
- Allow UV_EXTRA_INDEX_URL to be passed through (#294)
- Set bin marimushka (#299)
- Replace uv installation with setup-uv action (#311)
- Set working directory for subprocess execution (#309)
- Rename project from Config Templates to Rhiza (#1)
- Config-templates still in README and sync.sh (#5)
- Normalize organization name to lowercase in repository references (#8)
- More jebel-quant for Jebel-Quant
- Remove tests for conftest.py paritally
- 12 correct marimoyml (#13)
- Update test for repository root checks
- Add a logo and update readme (#14)
- Improve release output (#16)
- Simplify codespace (#17)
- Info for users (#24)
- Moving README.md into test_rhiza
- Extend available Templates (#25)
- Add comprehensive integration guide for existing projects (#23)
- Update README for sync mechanism instructions

<!-- generated by git-cliff -->
