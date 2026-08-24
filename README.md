<div align="center" markdown>

# <img src="https://raw.githubusercontent.com/Jebel-Quant/rhiza/main/bundles/book/docs/assets/rhiza-logo.svg" alt="Rhiza Logo" width="30" style="vertical-align: middle;"> Rhiza
![GitHub Release](https://img.shields.io/github/v/release/jebel-quant/rhiza?sort=semver&color=2FA4A9&label=rhiza)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python versions](https://img.shields.io/badge/Python-3.11%20•%203.12%20•%203.13%20•%203.14-blue?logo=python)](https://www.python.org/)
[![CI](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_ci.yml/badge.svg?event=push)](https://github.com/Jebel-Quant/rhiza/actions/workflows/rhiza_ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg?logo=ruff)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![CodeFactor](https://www.codefactor.io/repository/github/jebel-quant/rhiza/badge)](https://www.codefactor.io/repository/github/jebel-quant/rhiza)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/Jebel-Quant/rhiza/badge)](https://scorecard.dev/viewer/?uri=github.com/Jebel-Quant/rhiza)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/jebel-quant/rhiza)

# Strong roots
Creating and maintaining technical harmony across repositories.

A collection of reusable configuration templates
for modern Python, Rust and Go projects.
Save time and maintain consistency across your projects
with these pre-configured templates.

![Last Updated](https://img.shields.io/github/last-commit/jebel-quant/rhiza/main?label=Last%20updated&color=blue)

In the original Greek, spelt **ῥίζα**, pronounced *ree-ZAH*, and having the literal meaning **root**.

</div>

## 🌟 Why Rhiza?

Cookiecutter and copier generate a project once and then let go of it. Rhiza keeps the
connection: your configuration is **synced** from a template repository, so improvements to CI
workflows, linting rules and tooling reach every project that follows it — on your schedule, and
only where you allow. For the full comparison, see
[Why not copier or cruft?](docs/reference/WHY_NOT_COPIER_CRUFT.md).

### Rhiza and its companions

This repository is the *template content* only. Everything that **acts** on that content — syncing it, running the gates it configures, checking the result — lives in a separate, independently versioned package:

| Component | What it is | How you get it |
|-----------|------------|----------------|
| **[rhiza](https://github.com/jebel-quant/rhiza)** (this repository) | The template content: bundles of config files, CI/CD workflow stubs, and docs | Synced into your project |
| **[rhiza-claude](https://github.com/Jebel-Quant/rhiza-claude)** | The Claude Code plugin that drives adoption — `/rhiza:init`, `/rhiza:update`, `/rhiza:status`, `/rhiza:quality`, `/rhiza:docs`, `/rhiza:release` | `/plugin install rhiza@rhiza-claude` |
| **[rhiza-task](https://pypi.org/project/rhiza-task/)** | The task runner behind every target the `Makefile` forwards: `install`, `test`, `fmt` and every gate | Pinned as `RHIZA_TASK` in the synced `Makefile`, run through `uvx` |
| **[pytest-rhiza](https://github.com/jebel-quant/pytest-rhiza)** | The conformance checks a managed repo runs against itself (`make rhiza-test`) | Installed by that gate, at the version pinned in `[tool.rhiza-task]` |
| **[rhiza-hooks](https://github.com/Jebel-Quant/rhiza-hooks)** | The Rhiza-specific hooks named by the synced `.pre-commit-config.yaml` | Pinned by that config |

In short: **rhiza** is the *what* (the template files you receive); the companions are the *how*.

> **⚠️ `rhiza-cli` is retired.** `uvx rhiza init` and `uvx rhiza sync`, which earlier versions
> of this README documented, no longer work: the package is unpublished and
> [its repository](https://github.com/Jebel-Quant/rhiza-cli) archived. Its sync now ships
> inside the Claude Code plugin, so beyond `uv`, `git` and `make` there is nothing to install
> but the plugin itself.

### How It Works

One file, `.rhiza/template.yml`, says which template you follow and what you want from it:

```yaml
repository: "Jebel-Quant/rhiza"
ref: "v1.5.1"

profiles:
  - github-project
```

A **profile** is a named preset that expands to a set of **bundles**; you can add individual
bundles alongside it, and `include`/`exclude` patterns for the last mile. `ref` is a tag, so
Renovate can raise it for you — its manager only matches the quoted form shown above, which is
what `/rhiza:init` writes.

`/rhiza:update` then fetches what your selection owns and three-way merges it into a branch, so
local edits survive and you review the result as a pull request.

**The anatomy of that file, the sync lifecycle and the Renovate wiring are
[rhiza-education](https://github.com/Jebel-Quant/rhiza-education) Lessons 7–9** — this README
does not try to teach them.

## 📚 Table of Contents

- [Why Rhiza?](#-why-rhiza)
- [Quick Start](#-quick-start)
- [What You Get](#-what-you-get)
- [Available Templates](#-available-templates)
- [Integration Guide](#-integration-guide)
- [Available Tasks](#-available-tasks)
- [Customising Safely](#-customising-safely)
- [Documentation Map](#-documentation-map)
- [Learning Resources](#-learning-resources)
- [Contributing to Rhiza](#-contributing-to-rhiza)

## 🚀 Quick Start

Rhiza is driven from [Claude Code](https://claude.com/claude-code). Install the plugin once:

```text
/plugin marketplace add Jebel-Quant/rhiza-claude
/plugin install rhiza@rhiza-claude
```

Then, from your project directory:

```text
/rhiza:init      # write .rhiza/template.yml (the pointer) — merge that PR
/rhiza:update    # the first sync: brings the template content in — merge that PR too
/rhiza:quality   # score the result
```

**Bootstrapping is two pull requests, not one.** `/rhiza:init` writes the pointer and syncs
nothing, so its PR looks almost empty — that is correct. `/rhiza:update` is what delivers the
workflows, the `Makefile` and the rest, which keeps one code path responsible for
materialising template files.

More options are in the [Integration Guide](#-integration-guide); the step-by-step version is
[rhiza-education Lesson 6](https://github.com/Jebel-Quant/rhiza-education/blob/main/lessons/06-getting-started.md).
To work on Rhiza itself rather than use it, see [Contributing](#-contributing-to-rhiza).

## ✨ What You Get

Adopt a Rhiza bundle and your project immediately gains:

- **A `Makefile` front door** — a thin shim that pins `RHIZA_TASK` and forwards 40+ tasks (install, test, fmt, the gates, docs, release) to that CLI
- **A language layer** — Python, Rust or Go: one set of target names (`install`, `test`, `coverage`, `typecheck`, `security`, `license`, `deps`), a different engine behind each
- **CI/CD workflows** for GitHub Actions and/or GitLab CI — test, lint, release, docs
- **Pre-commit hooks** run by [prek](https://github.com/j178/prek) — ruff, bandit, markdownlint, interrogate, actionlint, and the `rhiza-hooks` checks
- **pytest** with coverage, benchmarks, and property-based testing via Hypothesis
- **Documentation** via MkDocs + zensical, with optional Marimo notebook exports
- **Release automation** — version bumping, OIDC PyPI publishing, optional grayskull conda recipe generation (`vars.PUBLISH_CONDA`, defaults to `true`), SLSA provenance
- **Security scanning** — CodeQL, bandit, secret scanning, Dependabot

## 📁 Available Templates

Bundles are the atomic unit: each owns a coherent set of files, and any bundle can be selected
on its own — its dependencies resolve automatically. Profiles compose them for common contexts.

### Profiles (Recommended Starting Point)

Rhiza provides **profiles** — named presets that select a sensible set of bundles for common project contexts. Profiles are the recommended way to get started.

| Profile | Description | Includes |
|---------|-------------|---------|
| `local` | Local-first development with no hosted CI/CD workflow files | `core`, `python-core`, `book`, `marimo`, `tests` |
| `rust-local` | Local-first Rust development, no hosted CI/CD (hosted profiles arrive with the Rust workflows) | `core`, `rust-core`, `book` |
| `go-local` | Local-first Go development, no hosted CI/CD (hosted profiles arrive with the Go workflows) | `core`, `go-core`, `book` |
| `github-project` | GitHub-hosted project with CI/CD and release automation | `core`, `python-core`, `github`, `book`, `marimo`, `tests`, `github-book`, `github-marimo`, `github-tests` |
| `gitlab-project` | GitLab-hosted project with GitLab CI/CD pipelines | `core`, `python-core`, `gitlab`, `book`, `marimo`, `tests`, `gitlab-book`, `gitlab-marimo`, `gitlab-tests` |

Declare a profile in `.rhiza/template.yml`:

```yaml
repository: "Jebel-Quant/rhiza"
ref: "v1.5.1"

profiles:
  - github-project
```

> **Note:** Profiles expand to their constituent bundles including all transitive requirements.

You can combine a profile with additional bundles:

```yaml
profiles:
  - github-project
templates:
  - docker
  - github-docker
```

### Available Template Bundles

Bundles are the atomic building blocks. Feature bundles are **local-first** — they do not include hosted workflow files. Platform overlay bundles (prefixed `github-` or `gitlab-`) add the CI/CD workflows for a given feature.

Any bundle can be selected on its own — its dependencies are resolved and installed automatically. The *Auto-installs* column shows which bundles are pulled in transitively when you select that bundle.

**Feature bundles**

| Bundle | Description | Auto-installs |
|--------|-------------|---------------|
| `core` | Core Rhiza infrastructure, language-neutral (the `Makefile` shim that pins `RHIZA_TASK`, editor and changelog config, uv as tool runner) | — |
| `python-core` | Python language layer (`install`/`all`, virtualenv, ruff, bandit, deptry) | `core` |
| `rust-core` | Rust language layer (`install`/`all`, cargo, clippy, nextest, llvm-cov, cargo-deny) | `core` |
| `go-core` | Go language layer (`install`/`all`, go test, golangci-lint, govulncheck, revive) | `core` |
| `tests` | Optional Python testing extras — the `benchmark`, `hypothesis-test` and `stress` gates (`test`, `coverage` and `typecheck` live in the language layer) | `book`, `core`, `python-core` |
| `book` | Comprehensive documentation book (API docs, coverage, notebooks) | `core` |
| `marimo` | Interactive Marimo notebooks for data exploration and documentation | `book`, `core`, `python-core` |
| `benchmarks` | Performance benchmarking with pytest-benchmark and reporting | `tests` |
| `docker` | Docker containerization support | — |
| `devcontainer` | VS Code DevContainer configuration | — |
| `vscode` | VS Code recommended extensions and workspace settings for local editing | — |
| `presentation` | Presentation building using Marp | — |
| `paper` | LaTeX paper compilation targets (`make paper`, `make paper-clean`) | — |
| `lfs` | Git LFS (Large File Storage) support | — |
| `legal` | Legal and community files (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT) | — |
| `renovate` | Renovate bot configuration for automated dependency updates | — |

**Platform bundles — GitHub**

| Bundle | Description | Auto-installs |
|--------|-------------|---------------|
| `github` | Base GitHub repository automation (sync, release, dependabot) | `core` |
| `github-tests` | GitHub Actions workflows for test automation (CI, CodeQL, weekly) | `github`, `tests`, `core` |
| `github-book` | GitHub Actions workflow for documentation publishing | `github`, `book`, `core` |
| `github-marimo` | GitHub Actions workflow for Marimo notebook automation | `github`, `marimo`, `book`, `core` |
| `github-docker` | GitHub Actions workflow for Docker image building and publishing | `github`, `docker`, `core` |
| `github-devcontainer` | GitHub Actions workflow for DevContainer image publishing | `github`, `devcontainer`, `core` |
| `github-paper` | GitHub Actions workflow for LaTeX paper compilation — the PDF is a run artifact, and ships durably as a book asset | `github`, `paper`, `core` |
| `github-quality-review` | Advisory Claude design review of PR diffs — architecture, complexity, test gaps (opt-in) | `github`, `core` |

**Platform bundles — GitLab**

| Bundle | Description | Auto-installs |
|--------|-------------|---------------|
| `gitlab` | GitLab CI/CD pipeline configuration and core workflows | `core` |
| `gitlab-tests` | GitLab CI pipeline for test automation | `gitlab`, `tests`, `core` |
| `gitlab-marimo` | GitLab CI pipeline for Marimo notebook execution | `gitlab`, `marimo`, `book`, `core` |
| `gitlab-book` | GitLab CI pipeline for documentation publishing to GitLab Pages | `gitlab`, `book`, `core` |
| `gitlab-quality-review` | Advisory Claude design review of MR diffs — architecture, complexity, test gaps (opt-in) | `gitlab`, `core` |

For a complete reference of every file included in each bundle, see [`.rhiza/template-bundles.yml`](.rhiza/template-bundles.yml).

## 🧩 Integration Guide

**Prerequisites:** [Claude Code](https://claude.com/claude-code) with the `rhiza` plugin,
[uv](https://docs.astral.sh/uv/), Git, GNU Make 3.81+, and a toolchain for your language (`uv`
manages the Python one). A `python-core` project also needs a `[project]` table in
`pyproject.toml` and a `.python-version`; a Rust or Go project needs neither.

Run `/rhiza:init`, merge, then `/rhiza:update`. Afterwards:

| Command | What it tells you |
|---------|-------------------|
| `/rhiza:status` | What the pointer says, and what the last sync actually delivered |
| `/rhiza:status --check` | Whether the template has moved on — read-only |
| `/rhiza:update v1.4.2` | Sync a specific release rather than the latest |
| `/rhiza:quality` | A score for the result, with findings |
| `/rhiza:detach` | Stop being template-managed, keeping the files |
| `make doctor` | Whether your local tools and versions are what the gates expect |

**A worked first run — empty directory to synced, scored repository — is
[rhiza-education Lesson 6](https://github.com/Jebel-Quant/rhiza-education/blob/main/lessons/06-getting-started.md).**
For sync failures and recovery, see [docs/troubleshooting.md](docs/troubleshooting.md).

## 📋 Available Tasks

The synced [`Makefile`](Makefile) is a shim: it pins `RHIZA_TASK` and forwards every unmatched target to that CLI, so `make test` resolves because `test` is a *task* — not because anything in the `Makefile` mentions it. `make` stays the front door (it is what CI calls and what a stranger types), but the tasks come from [rhiza-task](https://pypi.org/project/rhiza-task/), and `uvx rhiza-task list` is the authoritative list for the pinned version.

### Key Commands

```bash
make install         # Install dependencies and setup environment
make test            # Run test suite with coverage
make fmt             # Format and lint code
make todos           # Scan for TODO/FIXME/HACK comments
make marimo          # Start Marimo notebook server
make book            # Build documentation
```

Run `make help` for a complete list of 40+ available targets.

<details>
<summary>Show all available targets</summary>

<!-- MAKE_HELP_START -->
```text
 task                section         needs                 does                 
 book                Book            test benchmark        build the companion  
                                     stress                book                 
                                     hypothesis-test                            
                                     paper                                      
 book-nav            Book                                  check that every     
                                                           mkdocs nav entry     
                                                           resolves in the      
                                                           built book           
 marimo              Book            install               start the Marimo     
                                                           editor               
 marimo-validate     Book            install               check that every     
                                                           Marimo notebook runs 
 serve               Book            book                  build the book and   
                                                           serve it on port     
                                                           8000                 
 clean               Dev                                   remove build         
                                                           artifacts and stale  
                                                           local branches       
 doctor              Dev                                   check local          
                                                           prerequisites        
 docker-build        Docker                                build the Docker     
                                                           image                
 docker-clean        Docker                                remove the Docker    
                                                           image                
 docker-run          Docker          docker-build          run the Docker       
                                                           container            
 lfs-install         Git LFS                               configure git-lfs    
                                                           for this repository  
 lfs-pull            Git LFS                               download the LFS     
                                                           files for the        
                                                           current branch       
 lfs-status          Git LFS                               show the status of   
                                                           LFS files            
 lfs-track           Git LFS                               list the patterns    
                                                           tracked by git-lfs   
 failed-workflows    GitHub Helpers                        list recent failing  
                                                           workflow runs        
 latest-release      GitHub Helpers                        show information     
                                                           about the latest     
                                                           GitHub release       
 view-issues         GitHub Helpers                        list open issues     
 view-prs            GitHub Helpers                        list open pull       
                                                           requests             
 whoami              GitHub Helpers                        check github auth    
                                                           status               
 workflow-status     GitHub Helpers                        show recent runs for 
                                                           the release workflow 
 paper               Paper                                 compile the LaTeX    
                                                           paper to PDF         
 paper-clean         Paper                                 remove the LaTeX     
                                                           build artifacts      
 presentation        Presentation                          generate the HTML    
                                                           slides with Marp     
 presentation-pdf    Presentation                          generate the PDF     
                                                           slides with Marp     
 presentation-serve  Presentation                          serve the slides     
                                                           with Marp's live     
                                                           preview              
 all                 Python          fmt deps test         run every gate, as   
                                     docs-coverage         CI does              
                                     security license                           
                                     typecheck rhiza-test                       
 coverage            Python          install               measure coverage and 
                                                           write                
                                                           _tests/coverage.xml  
 deps                Python          install               run deptry over the  
                                                           contributed folders  
 docs-coverage       Python          install               check docstring      
                                                           coverage with        
                                                           interrogate          
 install             Python                                create the venv and  
                                                           sync dependencies    
 license             Python          install               scan for copyleft    
                                                           licences             
 security            Python          install               run the bandit       
                                                           security scan        
 test                Python          install               run all tests        
 typecheck           Python          install               run ty and/or mypy   
                                                           (typechecker = ty |  
                                                           mypy | both)         
 docs-examples       Quality         install               check the fenced     
                                                           examples in the docs 
                                                           tree                 
 fmt                 Quality                               run the pre-commit   
                                                           hooks over all files 
 complexity          Quality                               fail on a block      
                                                           above the            
                                                           cyclomatic-complexi… 
                                                           ceiling              
 test-pyproject      Quality         install               run the              
                                                           pyproject.toml       
                                                           structure checks,    
                                                           verbosely            
 rhiza-test          Quality         install               run the rhiza        
                                                           repository checks    
 semgrep             Quality                               run the semgrep      
                                                           static analysis      
                                                           rules                
 todos               Quality                               list every TODO,     
                                                           FIXME and HACK       
                                                           comment              
 benchmark           Testing extras  install               run the performance  
                                                           benchmarks           
 hypothesis-test     Testing extras  install               run the              
                                                           property-based tests 
 stress              Testing extras  install               run the stress and   
                                                           load tests           

Repo-owned targets:
  explain-bundles --  print all bundles and profiles with descriptions and dependencies
  sync-self --  relink root dogfood copies as symlinks into bundles/ (mother repo only)
  sync-self-check --  fail if any dogfood symlink is stale/missing without writing (local drift check)
  e2e --  run the language-layer end-to-end suite against real toolchains (opt-in)
```
<!-- MAKE_HELP_END -->

</details>

> **Note:** The help output is automatically generated from the Makefile.
> When you modify Makefile targets, the `update-readme-help` pre-commit hook
> updates this section automatically.

## 🎯 Customising Safely

Everything a sync delivers is **template-owned and overwritten by the next one** — the
`Makefile` included, since `core` ships it. Extensions live in five places no sync touches:

| Where | For |
|-------|-----|
| `local.mk` | Your own make targets, and extending a template task by shadowing it |
| `local-setup.sh` | Native binaries your project needs before any gate can run |
| `[tool.rhiza-task]` in `pyproject.toml` (or `rhiza.toml`) | Settings — `source-folder`, `coverage-fail-under`, … |
| `pyproject.toml` | Dependencies, scripts, other tools' configuration |
| `.rhiza/.env` | Developer-local overrides (gitignored) |

`local.mk` is deliberately **not** gitignored: commit it, because anything CI invokes has to be
in the repository.

### Makefile Customisation

The `Makefile` pins `RHIZA_TASK`, and that pin is the whole version contract: syncing a newer
template moves your gates forward. A `%:` catch-all forwards unmatched targets to that CLI, and
an explicit rule always beats it:

- **Add a target** — write it in `local.mk`, which the `Makefile` `-include`s. A `##` comment
  puts it in `make help` under *Repo-owned targets*.
- **Extend a task** — shadow it. An explicit `install:` rule can call `uvx $(RHIZA_TASK) install`
  and then your extra step. This replaces the `pre-install::` / `post-install::` hooks the synced
  make layer anchored, which are gone.
- **Change a setting** — the table above. `uvx rhiza-task list` shows the tasks and
  `uvx rhiza-task print <setting>` what one currently resolves to.

Worked examples: [CUSTOMIZATION.md](docs/guides/CUSTOMIZATION.md) and
[EXTENDING_RHIZA.md](docs/guides/EXTENDING_RHIZA.md). The tutorial version is
[rhiza-education Lesson 10](https://github.com/Jebel-Quant/rhiza-education/blob/main/lessons/10-customizing-safely.md).

### Documentation Examples

README code blocks are executable documentation. With the `tests` bundle selected,
`make rhiza-test` runs each `python` fence and diffs its output against the `result` block that
follows, so an example cannot quietly stop working.

```python
# Example code block
import math
print("Hello, World!")
print(1 + 1)
print(round(math.pi, 2))
print(round(math.cos(math.pi/4.0), 2))
```

```result
Hello, World!
2
3.14
0.71
```

## 📚 Documentation Map

| Topic | Where |
|-------|-------|
| Command and file cheat sheet | [QUICK_REFERENCE.md](docs/guides/QUICK_REFERENCE.md) |
| Every bundle and profile | [BUNDLE_TAXONOMY.md](docs/reference/BUNDLE_TAXONOMY.md) |
| Terms used throughout | [GLOSSARY.md](docs/reference/GLOSSARY.md) |
| The tools in the stack | [TOOLS_REFERENCE.md](docs/reference/TOOLS_REFERENCE.md) |
| Docs site (MkDocs + zensical) | [BOOK.md](docs/guides/BOOK.md) |
| Marimo notebooks · Marp slides | [MARIMO.md](docs/development/MARIMO.md) · [PRESENTATION.md](docs/development/PRESENTATION.md) |
| Dev containers · Docker | [DEVCONTAINER.md](docs/development/DEVCONTAINER.md) · [DOCKER.md](docs/development/DOCKER.md) |
| Releases and the changelog | [CHANGELOG_GUIDE.md](docs/ops/CHANGELOG_GUIDE.md) |
| What CI enforces, and where | [CI_ENFORCEMENT.md](docs/operations/CI_ENFORCEMENT.md) |
| Technical debt · roadmap | [TECHNICAL_DEBT.md](docs/ops/TECHNICAL_DEBT.md) · [PROJECT_BOARD.md](docs/ops/PROJECT_BOARD.md) |
| One patch across many bundles | [GLOBAL_PATCH.md](docs/ops/GLOBAL_PATCH.md) |

**Private packages:** the workflows already configure git authentication with the default
`GITHUB_TOKEN`, so a `[tool.uv.sources]` entry pointing at another repository in the same
organisation works with no extra setup.

## 🔄 CI/CD Support

GitHub Actions and GitLab CI have feature parity: tests across operating systems and Python
versions, hooks and gates, docs publishing, notebooks, containers, releases, security scanning
and weekly maintenance. Choose the platform by profile — `github-project` or `gitlab-project` —
and the matching workflow stubs arrive with it. Syncing is not a workflow: `/rhiza:update` runs
it from your machine and opens the PR.

GitLab specifics (variables, runners, Pages) are in
**[.gitlab/README.md](bundles/gitlab/.gitlab/README.md)**; what each check enforces and where it
runs is in [CI_ENFORCEMENT.md](docs/operations/CI_ENFORCEMENT.md).

## 📖 Learning Resources

This README is a reference. The **tutorial** is a separate repository, and the better place to
start if any of this is new:

**[jebel-quant/rhiza-education](https://github.com/Jebel-Quant/rhiza-education)** ·
[rendered site](https://jebel-quant.github.io/rhiza-education/)

Twelve lessons in order, from the problem living templates solve to running your first sync:
CI/CD concepts and `uv` (1–2), Python project conventions (3), why Rhiza and its core concepts
(4–5), **getting started** (6), configuring `template.yml` (7), the sync lifecycle (8), Renovate
(9), customising safely (10), the wider ecosystem (11), further reading (12). Appendices cover
GitLab users and real projects using Rhiza.

## 🛠️ Contributing to Rhiza

To work on Rhiza itself, you need GNU Make, Git and `uv`; `make install` provisions the rest,
Python included.

```bash
git clone https://github.com/jebel-quant/rhiza.git
cd rhiza
make install
make test && make fmt
```

Branch, commit, open a PR. [CONTRIBUTING.md](.rhiza/CONTRIBUTING.md) has the conventions,
[TESTS.md](docs/development/TESTS.md) explains the suite's layout, and
[EXTENDING_RHIZA.md](docs/guides/EXTENDING_RHIZA.md) is the checklist for adding a bundle.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [GitHub Actions](https://github.com/features/actions) - For CI/CD capabilities
- [Marimo](https://marimo.io/) - For interactive notebooks
- [UV](https://github.com/astral-sh/uv) - For fast Python package operations
- [Ruff](https://github.com/astral-sh/ruff) - For Python linting and formatting
- [Marp](https://marp.app/) - For presentation generation
