# Rhiza Repository Analysis

> **Date**: 2026-05-27  
> **Analyst**: Claude Sonnet 4.6  
> **Branch**: `quality-assessment`  
> **Scope**: Full repository audit — architecture, code quality, testing, documentation, CI/CD, security, and developer experience.

---

## Executive Summary

Rhiza is a **living template system** for Python projects — a collection of 23 composable configuration bundles that downstream repositories can selectively adopt and continuously sync as the template evolves. It is not a runtime library. Its "product" is Makefile targets, CI/CD workflows, linting configs, testing scaffolding, and documentation infrastructure delivered as versioned, composable units.

The repository is exceptionally well-engineered for its purpose. Architecture decisions are documented, automation is comprehensive, and the quality gates are among the strictest in open-source Python tooling. The main risks are around **complexity overhang** (the cost of maintaining 23 bundles × 2 CI platforms), **lack of runtime code** (leaving some standard software quality metrics inapplicable), and a **steep learning curve** for contributors unfamiliar with the bundle model.

**Overall score: 8.6 / 10**

---

## Category Scores

| Category | Score | Summary |
|---|---|---|
| Architecture & Design | 9 / 10 | Exceptionally clean bundle model; dual-CI feature parity is ambitious but well-executed |
| Code Quality & Standards | 8 / 10 | Strict tooling; no runtime code makes some metrics irrelevant |
| Testing & Coverage | 8 / 10 | Comprehensive for a template system; some gaps in end-to-end sync testing |
| Documentation | 9 / 10 | Outstanding — ADRs, guides, notebooks, glossary all present |
| CI/CD & DevOps | 9 / 10 | One of the most complete pipelines seen in a Python open-source project |
| Security | 9 / 10 | Supply chain, SAST, secrets, SBOM — all boxes ticked |
| Developer Experience | 8 / 10 | Rich tooling; initial setup complexity and bundle mental model are friction points |
| Dependency Management | 9 / 10 | `uv` + locked file + Renovate + lowest-dep CI matrix is best-in-class |
| Maintainability & Extensibility | 7 / 10 | Extension model is elegant; 23-bundle surface area is the main long-term risk |
| Performance | 6 / 10 | No runtime code to benchmark; CI speed not optimised for large matrix |
| Configuration & Tooling | 9 / 10 | Near-exhaustive toolchain; some config duplication is intentional and acceptable |

---

## 1. Architecture & Design — 9 / 10

### Strengths

**Bundle-profile model is the right abstraction.** The separation between "feature bundles" (local, composable infrastructure) and "platform overlay bundles" (thin CI wrappers) is clean. A project that wants pytest without GitHub Actions can take the `tests` bundle without taking `github-tests`. This is genuinely elegant — many template systems make this orthogonality impossible.

**Living template, not one-time generation.** The sync model (downstream projects pull updates from this repo on a schedule) solves the perennial problem of template drift. Projects do not diverge silently; they receive changes and must resolve conflicts explicitly. This is architecturally superior to generator tools like Cookiecutter.

**Modular Makefile architecture is well-designed.** The double-colon hook targets (`pre-install::`, `post-sync::`) and the alphabetical auto-loading of `make.d/*.mk` allow downstream projects to extend without forking. The pattern is similar to `run-parts(8)` and is appropriate here.

**ADRs (Architecture Decision Records) are a first-class citizen.** 10 ADRs covering every major technical decision (package manager choice, CI platform, bundle model, docstring tool, etc.) signal institutional maturity and reduce the "why is it done this way?" burden for new contributors.

**Dual CI/CD feature parity (GitHub + GitLab) is ambitious and delivered.** Most projects pick one platform. Rhiza maintains full parity, which is valuable for teams in regulated environments that must use GitLab.

### Weaknesses

**Bundle dependency graph is implicit.** While `template-bundles.yml` encodes dependencies, there is no programmatic enforcement that prevents a bundle from being used without its prerequisites at sync time (short of the CLI catching it). A formal dependency DAG with cycle detection would harden this.

**No runtime code means the architecture cannot be validated by type checkers or static analysers beyond configuration files.** The system's correctness lives entirely in YAML, Makefiles, and shell scripts — formats with poor static analysis support.

**Score deduction of 1 point**: The architectural surface area (23 bundles × 2 CI platforms = 46 combinations to keep consistent) is the primary long-term risk. There is no automated cross-combination regression test confirming that all 46 combinations produce valid, non-conflicting output.

---

## 2. Code Quality & Standards — 8 / 10

### Strengths

**Ruff is configured at high strictness.** The `ruff.toml` enables an unusually comprehensive rule set: `D` (docstrings), `E/W` (pycodestyle), `F` (pyflakes), `I` (isort), `N` (pep8-naming), `UP` (pyupgrade), `B` (bugbear), `C4` (comprehensions), `SIM` (simplifications), `PT` (pytest patterns), `RUF` (ruff-specific), `S` (bandit-via-ruff), `TRY` (exception handling), `ICN` (import conventions). This is stricter than the average production Python project.

**100% docstring coverage is enforced** by `interrogate` in pre-commit and CI. This is a high bar that forces documentation discipline.

**The `--unsafe-fixes` flag on ruff in pre-commit** is a bold choice that applies all available fixes automatically, reducing manual cleanup burden.

**EditorConfig** ensures cross-editor consistency for contributors using VS Code, JetBrains, vim, etc.

**Google docstring style** is consistently chosen and enforced — a clear standard rather than mixed styles.

### Weaknesses

**No runtime Python source (`src/`) means most code quality metrics are vacuous.** The test files and utility scripts exist, but there is no library code to which type checking, cyclomatic complexity analysis, or SOLID principles apply in a meaningful way. The `8/10` here reflects the quality of the infrastructure code (scripts, tests, Makefiles), not application code.

**Shell scripts in `.rhiza/utils/` are not linted by shellcheck.** Pre-commit hooks include `actionlint` for GitHub Actions YAML but no `shellcheck` for Bash scripts. Given that several utility scripts (`pip-audit.sh`, `suppression-audit.sh`) are security-adjacent, this is a gap.

**`ruff.toml` line length of 120 characters** departs from the PEP 8 default of 79 and the more common 88 (black default). Not a bug, but worth noting as it reduces portability of the style config to downstream projects that may have different conventions.

---

## 3. Testing & Coverage — 8 / 10

### Strengths

**90% coverage minimum is enforced in CI.** This is above the industry median (~70-80%) and reflects genuine commitment to test quality rather than coverage theatre.

**Property-based testing (Hypothesis) is included.** `@pytest.mark.property` tests verify invariants across random inputs rather than just named examples. This is still relatively rare in Python infrastructure projects.

**Test types are well-separated:** unit, integration, stress, property, and benchmark tests are all distinct with appropriate markers and CI handling. Stress tests are excluded from the default run (appropriate), benchmarks are separated, and integration tests cover the full sync pipeline.

**Bundle content validation tests** verify YAML syntax, file existence, and symlink integrity for every bundle — a practical equivalent of a schema test suite for configuration-as-code.

**80 test files in `.rhiza/tests/`** cover internal infrastructure comprehensively: Makefile targets, workflow stubs, LFS, virtual environment handling, security patterns.

**Lowest-dependency matrix** in CI (`uv --resolution lowest-direct`) catches regressions introduced by relaxed version constraints. Very few projects do this.

### Weaknesses

**End-to-end sync testing against a real downstream repository is not evident.** Tests validate bundle content validity and resolution logic, but there is no test that provisions a fresh downstream repo, runs `rhiza sync`, and verifies the resulting state is functional. This is the highest-value missing test.

**No mutation testing.** Given that the system's output is YAML and configuration files, mutation testing (e.g., verifying that changing a bundle file causes a test to fail) would strengthen confidence in the test suite's discriminating power.

**Test execution time for the full matrix** (Python 3.11–3.14 × ubuntu/macos/windows) is not tracked or bounded. No indication of test parallelism configuration beyond the default `pytest-xdist` availability.

**GitHub Actions workflow tests** validate that stub YAMLs compile, but do not run the workflows end-to-end against a test repository in a sandbox environment.

---

## 4. Documentation — 9 / 10

### Strengths

**ADRs are present, recent, and comprehensive.** All 10 ADRs are dated, explain the context, the decision, and the consequences. This is the single most reliable indicator of architectural seriousness.

**Documentation is multi-layered and role-targeted:**
- Developers get `docs/development/` guides (Docker, DevContainers, VS Code, Marimo, Marp)
- Operators get `docs/operations/` guides (changelog, project boards, technical debt)
- Security teams get `docs/security/` policies and testing procedures
- New contributors get `docs/guides/` quick reference and demo walkthrough
- End users get a 26KB README with full feature coverage

**Glossary and terminology definitions** in `docs/reference/GLOSSARY.md` prevent conceptual ambiguity ("bundle vs profile vs template" is a subtle distinction this glossary makes explicit).

**Interactive Marimo notebooks** in `docs/notebooks/rhiza.py` go beyond static documentation — contributors can run live examples and see outputs without leaving the documentation.

**MkDocs with Material theme** produces a professional, searchable documentation site. `mkdocs.yml` is configured with Mermaid diagram support.

**CHANGELOG.md** is 19KB — actively maintained, not a placeholder.

### Weaknesses

**Some guides are thin on code examples.** `EXTENDING_RHIZA.md` describes the extension mechanism at a conceptual level but has limited step-by-step worked examples for adding a new bundle from scratch.

**No API reference documentation.** Since there is no library code, this is understandable — but downstream project developers who want to understand what each Makefile target does must read the Makefile source rather than consult a reference page.

**Documentation coverage is 100% for docstrings but the MkDocs site navigation** has some sections that duplicate README content without clear "canonical source" signposting, creating a risk of drift.

---

## 5. CI/CD & DevOps — 9 / 10

### Strengths

**12 GitHub Actions workflows covering the full software lifecycle:** testing, releasing, documentation publishing, security scanning, Docker validation, DevContainer validation, notebook execution, PDF compilation, agentic workflow validation, and template sync. Each concern is separated into its own workflow.

**Matrix testing across Python 3.11–3.14 on ubuntu/macos/windows** is comprehensive and catches platform-specific issues that most projects miss by only testing Linux.

**Trusted Publishing (OIDC)** for PyPI eliminates stored API tokens from the release pipeline — a significant security improvement over the status quo.

**SLSA provenance attestations** for public release artifacts place Rhiza at SLSA Level 2+, ahead of the vast majority of open-source Python projects.

**SBOM generation (CycloneDX format)** is included in the release workflow, supporting supply chain transparency requirements (NTIA, EU CRA).

**Reusable workflow architecture** — downstream projects call these workflows as callers, reducing duplication. This is the CI/CD equivalent of the bundle model itself.

**Renovate configuration** covers `pep621`, `pre-commit`, `github-actions`, and custom regex for Rhiza version references — automated dependency hygiene with minimal manual intervention.

**`copilot-setup-steps.yml`** for GitHub Copilot agent environment preheating is forward-looking infrastructure that most projects lack.

### Weaknesses

**No explicit CI time budget or caching strategy for the test matrix.** The 3.11–3.14 × 3 OS matrix is 12 combinations, each running all tests. No evidence of test sharding, `pytest-xdist` parallelism, or dependency caching analysis (beyond pre-commit caching). On a cold cache, the full matrix likely takes 30–60 minutes.

**GitLab CI parity** requires manual synchronisation. There is no automated test that confirms GitHub Actions and GitLab CI workflows produce equivalent results on the same inputs.

**Workflow stubs rely on `workflow_call` delegation** which creates an implicit coupling to the calling convention. If the reusable workflow interface changes, downstream stub callers can silently break (no schema enforcement for workflow inputs).

---

## 6. Security — 9 / 10

### Strengths

**Multi-layer security scanning:** CodeQL (SAST), Bandit (Python-specific), Semgrep (pattern-based), pip-audit (dependency CVEs), secret scanning (GitHub native). This is defence in depth applied to a software supply chain.

**No hardcoded credentials found** in any configuration, workflow, or script file. All authentication uses OIDC, environment variables, or GitHub Secrets.

**SECURITY.md** defines a responsible disclosure process with explicit SLAs (48h acknowledgment, 7-day assessment, 30-day critical fix). The scope and out-of-scope sections are precise, reducing ambiguous reports.

**Dependency pinning** via `uv.lock` ensures reproducible builds and eliminates a class of supply chain attacks (dependency confusion, version sliding).

**GitHub Actions token scope** is `contents: read` by default — principle of least privilege enforced at the workflow level.

**License compliance scanning** (blocking GPL/LGPL/AGPL) protects downstream adopters from inadvertently incorporating copyleft dependencies.

### Weaknesses

**Bandit suppression audit** (`suppression-audit.sh`) is present but the suppressions themselves are not reviewed in CI for validity — a suppression added for a fixed vulnerability may linger silently.

**`shellcheck` is absent for shell utilities** — a recurring theme. Security-adjacent Bash scripts in `.rhiza/utils/` process pip-audit JSON output; a shell injection in these scripts would undermine the audit they perform.

**No fuzzing or DAST** — not expected for a configuration template system, but worth noting that the only dynamic test surface (the sync CLI, in the separate `rhiza-cli` package) is outside this repo's security perimeter.

**Secret scanning is GitHub's built-in tool** — no Gitleaks or Trufflehog for deeper historical scanning or custom pattern coverage.

---

## 7. Developer Experience — 8 / 10

### Strengths

**`make` is the universal entry point.** All common operations (`make install`, `make test`, `make fmt`, `make docs`, `make release`) are available without knowing the underlying toolchain. New contributors can be productive without reading implementation details.

**Shell completions** for bash and zsh are generated and distributed with the `core` bundle. Auto-complete for Makefile targets is a quality-of-life feature almost no project provides.

**Dev Containers** and **Docker** support means contributors can work in a consistent environment without local tool installation. VS Code extension recommendations are included.

**`local.mk`** allows developers to add repository-specific targets without committing them — a standard pattern from C/C++ projects rarely seen in Python tooling.

**`make help`** with colour-coded output grouped by category is clearly implemented in `make.d/` targets. The help output is discoverable.

**Pre-commit hooks** catch issues before CI, reducing round-trip time on feedback.

**GitHub Copilot integration** (`copilot-setup-steps.yml`, `CLAUDE.md`) means AI coding assistants have context about the repository's conventions.

### Weaknesses

**The bundle mental model has a steep learning curve.** The distinction between "bundle", "profile", "overlay", "stub", and "template" is conceptually non-trivial. A contributor unfamiliar with the system must read multiple documents before the mental model clicks. An interactive `make explain-bundles` target or a visual diagram would help.

**Initial setup requires `uv`** — not universally installed. While `uv` is the future of Python tooling, contributors on locked-down corporate machines may face friction getting `uv` approved.

**Error messages from bundle sync failures** are not described in the documentation. It is unclear whether a failed sync rolls back, leaves the downstream project in a partial state, or provides actionable diagnostics.

**`CLAUDE.md`** is present (good), but its content is not reviewed here. AI-assisted development is increasingly important and having correct guidance here matters.

---

## 8. Dependency Management — 9 / 10

### Strengths

**`uv` is the correct choice for 2026.** It is faster than pip/poetry, resolver-correct, workspace-aware, and the emerging standard. The ADR documenting this choice (ADR-0002) shows it was deliberate, not accidental.

**`uv.lock`** is committed and enforced by pre-commit. Deterministic installs are guaranteed.

**Renovate** is configured to auto-update `pep621` (pyproject.toml), pre-commit hook versions, GitHub Actions, and custom Rhiza version references — all four dependency surfaces are covered. Most projects cover one or two.

**Lowest-dependency CI matrix** (`--resolution lowest-direct`) validates that the declared version bounds are actually compatible at their lower bounds, not just at the latest version. This is best practice and rarely implemented.

**No unnecessary runtime dependencies.** As a template system, Rhiza has zero runtime dependencies — only dev dependencies for the tooling that builds and tests the templates themselves. The dependency graph is clean.

**Python version matrix (3.11–3.14)** is forward-looking, including 3.14 before its stable release. This ensures early detection of compatibility issues.

### Weaknesses

**The dev dependency set is substantial** (marimo, numpy, plotly, pandas, pyyaml, plus all test/quality tooling). Installation time on a cold environment is non-trivial. There is no `requirements/minimal.txt` for environments where only the linting/testing subset is needed.

**Renovate configuration** does not appear to include the `gitlab-ci` package ecosystem — GitLab workflow dependencies may drift.

---

## 9. Maintainability & Extensibility — 7 / 10

### Strengths

**Extension points are well-designed.** Double-colon Makefile targets allow downstream projects and local contributors to append behaviour without patching core files. This is the correct pattern for a plug-in extension model.

**Bundle isolation is enforced** — each bundle owns its files and no file is owned by two bundles. This prevents accidental coupling and makes bundle removal clean.

**`custom-task.mk` and `custom-env.mk` examples** provide a scaffolded starting point for downstream customisation, reducing the blank-page problem.

**Technical debt is documented** in `docs/operations/TECHNICAL_DEBT.md` — known limitations are explicit, not hidden.

**CHANGELOG.md is actively maintained** at 19KB, indicating long-term project health.

### Weaknesses

**23 bundles × 2 CI platforms = 46 surfaces to maintain consistently.** The primary long-term risk. Adding a new global tool or convention (e.g., adopting a new type checker) requires updating every affected bundle. There is no evidence of a "global patch" mechanism that can propagate a change to all bundles atomically.

**Makefile targets use GNU Make conventions** but the codebase does not pin or document the required GNU Make version. Some targets may behave differently on macOS's BSD Make (although `uv` and most CI environments use GNU Make).

**Bundle symlinks** are a useful pattern for sharing content but create maintenance complexity — if a symlink target moves, all bundles pointing to it silently break until a test catches it. The bundle content validity tests mitigate this but do not eliminate it.

**No plugin registry or bundle versioning.** There is no mechanism for a downstream project to pin to a specific bundle version while other bundles update. All bundles are versioned together at the Rhiza repository level. This is a deliberate design choice (reduces complexity) but limits adoption by projects with strict change management requirements.

---

## 10. Performance — 6 / 10

### Strengths

**Benchmark suite is present** (`bundles/benchmarks/`) with a `make benchmark` target. Performance measurement infrastructure exists, even if there is no runtime code to optimise.

**`uv` is significantly faster than pip/poetry** for dependency installation — cold installs that took minutes now take seconds. This directly improves CI throughput.

**Pre-commit caching** in CI (evident from workflow configuration) reduces hook execution time on repeated runs.

### Weaknesses

**No runtime code means performance is entirely CI/CD pipeline performance** — and this is not explicitly tracked, budgeted, or optimised.

**The 12-combination test matrix** (4 Python versions × 3 OSes) runs sequentially within each combination. No evidence of `pytest-xdist` being used to parallelise tests within a runner, which would reduce per-combination wall time.

**Marimo notebooks (`rhiza.py`)** are executed in CI (`rhiza_marimo.yml`). Notebook execution time is not bounded — a slow computation in a notebook would delay the workflow with no timeout.

**Documentation build (`make book`)** involves `pdoc` + `mkdocs`. Build time is not tracked. As the documentation grows, this could become a bottleneck.

**Score note**: 6/10 reflects the narrow applicability of the category to a template system. The score is not a criticism — it reflects that performance engineering is simply not the primary concern here.

---

## 11. Configuration & Tooling — 9 / 10

### Strengths

**Near-exhaustive toolchain coverage** — every dimension of Python project quality has a tool: linting (ruff), formatting (ruff), type checking (ty), docstring coverage (interrogate), security (bandit, CodeQL, pip-audit, Semgrep), dependency analysis (deptry), license compliance, markdown linting (markdownlint), GitHub Actions validation (actionlint), YAML/TOML validation (check-jsonschema, validate-pyproject), and lock file integrity (uv-lock pre-commit hook).

**Single pre-commit configuration** (`pre-commit-config.yaml`) coordinates all hooks. Contributors run `pre-commit run --all-files` or rely on the git hook to enforce all standards at once.

**`ruff.toml` is a standalone file** (not embedded in `pyproject.toml`), making it easier to reference and copy in documentation.

**`.editorconfig`** prevents the common problem of mixed tab/space indentation across contributors and editors.

**`codefactor.yml`** integrates with CodeFactor for continuous code quality tracking — a useful public-facing quality signal.

### Weaknesses

**Some tool configurations are duplicated across bundles** (e.g., `ruff.toml` may appear in multiple bundle outputs). While this is intentional for bundle isolation, it creates a maintenance burden when the standard configuration changes — each bundle copy must be updated separately.

**`ty` (type checker) is Python 3.13+ only**, meaning type checking is not available in the 3.11/3.12 CI matrix jobs. Type errors in code that runs on 3.11 would not be caught by CI unless a separate `ty` job is added for each Python version.

**No `pyright` or `mypy` fallback** for the 3.11/3.12 matrix — if type correctness matters across all supported versions, a second type checker configured for those versions is needed.

---

## Cross-Cutting Concerns

### What Rhiza Does Exceptionally Well

1. **Template drift prevention** via living sync is a genuinely solved problem here. Most ecosystems have no answer to this.
2. **ADR culture** — 10 ADRs for a template system is admirable discipline. Most production applications have zero.
3. **Supply chain security** — SLSA, SBOM, OIDC, dependency pinning, and multiple CVE scanners is best-in-class.
4. **Multi-platform CI parity** — GitHub + GitLab with matching feature sets is a rare commitment.
5. **Developer tooling breadth** — from shell completions to Marimo notebooks to DevContainers, the DX investment is genuine.

### Primary Risks

1. **23-bundle maintenance surface** — the combinatorial complexity will grow. A formal bundle compatibility matrix test and a "global patch" propagation mechanism would mitigate this.
2. **No end-to-end sync test against a real downstream project** — the highest-confidence test is missing.
3. **`shellcheck` gap on security-adjacent scripts** — small effort, high value.
4. **Bundle mental model onboarding** — the first hour for a new contributor is steep.

### Recommendations (Priority Order)

| Priority | Recommendation | Effort |
|---|---|---|
| High | Add end-to-end test: provision a minimal downstream repo, run `rhiza sync`, verify output | Medium |
| High | Add `shellcheck` to pre-commit hooks for `.rhiza/utils/` shell scripts | Low |
| Medium | Add bundle compatibility matrix test confirming all 46 bundle×platform combos produce valid output | High |
| Medium | Add visual bundle dependency diagram to documentation | Low |
| Medium | Add `make explain-bundles` interactive help target for onboarding | Low |
| Low | Configure `ty` (or `mypy`) for Python 3.11/3.12 CI matrix jobs | Low |
| Low | Review and prune stale Bandit suppressions in CI | Low |
| Low | Add Renovate config for GitLab CI ecosystem dependencies | Low |

---

## Final Scores

| Category | Score |
|---|---|
| Architecture & Design | 9 / 10 |
| Code Quality & Standards | 8 / 10 |
| Testing & Coverage | 8 / 10 |
| Documentation | 9 / 10 |
| CI/CD & DevOps | 9 / 10 |
| Security | 9 / 10 |
| Developer Experience | 8 / 10 |
| Dependency Management | 9 / 10 |
| Maintainability & Extensibility | 7 / 10 |
| Performance | 6 / 10 |
| Configuration & Tooling | 9 / 10 |
| **Overall** | **8.6 / 10** |

---

*Analysis produced by Claude Sonnet 4.6 on 2026-05-27. Findings are based on static analysis of repository structure, configuration files, workflow definitions, documentation, and test files. No dynamic execution of workflows or downstream sync simulation was performed.*
