# Rhiza Architecture

Visual diagrams of Rhiza's architecture and component interactions.

## System Overview

```mermaid
flowchart TB
    subgraph User["User Interface"]
        make[make commands]
        local[local.mk]
    end

    subgraph Core[".rhiza/ Core"]
        rhizamk[rhiza.mk<br/>Core Logic]
        maked[make.d/*.mk<br/>Extensions]
        scripts[scripts/<br/>Shell Scripts]
        utils[utils/<br/>Python Utils]
        template[template.yml<br/>Sync Config]
    end

    subgraph Config["Configuration"]
        pyproject[pyproject.toml]
        ruff[ruff.toml]
        precommit[.pre-commit-config.yaml]
        editorconfig[.editorconfig]
    end

    subgraph CI["GitHub Actions"]
        ci[CI Workflow]
        release[Release Workflow]
        security[Security Workflow]
        sync[Sync Workflow]
    end

    make --> rhizamk
    local -.-> rhizamk
    rhizamk --> maked
    rhizamk --> scripts
    rhizamk --> utils
    maked --> pyproject
    utils --> pyproject
    ci --> make
    release --> make
    security --> make
    sync --> template
```

## Makefile Hierarchy

```mermaid
flowchart TD
    subgraph Entry["Entry Point"]
        Makefile[Makefile<br/>9 lines]
    end

    subgraph Core["Core Logic"]
        rhizamk[.rhiza/rhiza.mk<br/>268 lines]
    end

    subgraph Extensions["Auto-loaded Extensions"]
        config[00-19: Configuration]
        tasks[20-79: Task Definitions]
        hooks[80-99: Hook Implementations]
    end

    subgraph Local["Local Customization"]
        localmk[local.mk<br/>Not synced]
    end

    Makefile -->|includes| rhizamk
    rhizamk -->|includes| config
    rhizamk -->|includes| tasks
    rhizamk -->|includes| hooks
    rhizamk -.->|optional| localmk
```

## Hook System

```mermaid
flowchart LR
    subgraph Hooks["Double-Colon Targets"]
        pre_install[pre-install::]
        post_install[post-install::]
        pre_sync[pre-sync::]
        post_sync[post-sync::]
        pre_release[pre-release::]
        post_release[post-release::]
        pre_bump[pre-bump::]
        post_bump[post-bump::]
    end

    subgraph Targets["Main Targets"]
        install[make install]
        sync[make sync]
        release[make release]
        bump[make bump]
    end

    pre_install --> install --> post_install
    pre_sync --> sync --> post_sync
    pre_release --> release --> post_release
    pre_bump --> bump --> post_bump
```

## Release Pipeline

```mermaid
flowchart TD
    tag[Push Tag v*] --> validate[Validate Tag]
    validate --> build[Build Package]
    build --> draft[Draft GitHub Release]
    draft --> pypi[Publish to PyPI]
    draft --> devcontainer[Publish Devcontainer]
    pypi --> finalize[Finalize Release]
    devcontainer --> finalize

    subgraph Conditions
        pypi_cond{Has dist/ &<br/>not Private?}
        dev_cond{PUBLISH_DEVCONTAINER<br/>= true?}
    end

    draft --> pypi_cond
    pypi_cond -->|yes| pypi
    pypi_cond -->|no| finalize
    draft --> dev_cond
    dev_cond -->|yes| devcontainer
    dev_cond -->|no| finalize
```

## Template Sync Flow

```mermaid
flowchart LR
    upstream[Upstream Rhiza<br/>jebel-quant/rhiza] -->|template.yml| sync[make sync]
    sync -->|updates| downstream[Downstream Project]

    subgraph Synced["Synced Files"]
        workflows[.github/workflows/]
        rhiza[.rhiza/]
        configs[Config Files]
    end

    subgraph Preserved["Preserved"]
        localmk[local.mk]
        src[src/]
        tests[tests/]
    end

    sync --> Synced
    downstream --> Preserved
```

## Directory Structure

```mermaid
flowchart TD
    root[Project Root]

    root --> rhiza[.rhiza/]
    root --> github[.github/]
    root --> src[src/]
    root --> tests[tests/]
    root --> docs[docs/]
    root --> book[book/]

    rhiza --> rhizamk[rhiza.mk]
    rhiza --> maked[make.d/]
    rhiza --> scripts[scripts/]
    rhiza --> utils[utils/]
    rhiza --> template[template.yml]

    github --> workflows[workflows/]
    workflows --> ci[rhiza_ci.yml]
    workflows --> release[rhiza_release.yml]
    workflows --> security[rhiza_security.yml]
    workflows --> more[... 11 more]

    maked --> m00[00-19: Config]
    maked --> m20[20-79: Tasks]
    maked --> m80[80-99: Hooks]
```

## CI/CD Workflow Triggers

```mermaid
flowchart TD
    subgraph Triggers
        push[Push]
        pr[Pull Request]
        schedule[Schedule]
        manual[Manual]
        tag[Tag v*]
    end

    subgraph Workflows
        ci[CI]
        security[Security]
        codeql[CodeQL]
        release[Release]
        deptry[Deptry]
        precommit[Pre-commit]
    end

    push --> ci
    push --> security
    push --> codeql
    pr --> ci
    pr --> deptry
    pr --> precommit
    schedule --> security
    manual --> ci
    tag --> release
```

## Python Execution Model

```mermaid
flowchart LR
    subgraph Commands
        make[make test]
        direct[Direct Python]
    end

    subgraph UV["uv Layer"]
        uv_run[uv run]
        uvx[uvx]
    end

    subgraph Tools
        pytest[pytest]
        ruff[ruff]
        hatch[hatch]
    end

    make --> uv_run
    uv_run --> pytest
    uv_run --> ruff
    uvx --> hatch

    direct -.->|Never| pytest

    style direct stroke-dasharray: 5 5
```

---

## Deep Dive: Component Interactions

### Makefile System

The Makefile system is modular and extensible:

**Core Components:**

1. **Entry Point (`Makefile`)** — Minimal 9-line file that includes `.rhiza/rhiza.mk`
2. **Core Logic (`.rhiza/rhiza.mk`)** — 268 lines of make targets and logic
3. **Extensions (`.rhiza/make.d/*.mk`)** — Auto-loaded modular files

**Extension Loading:**

```makefile
# From .rhiza/rhiza.mk
-include .rhiza/make.d/*.mk  # Load all extensions
-include local.mk             # Load local overrides (optional)
```

Files are loaded in alphabetical order, hence the numeric prefixes:

- `00-19*.mk` — Configuration and variables
- `20-79*.mk` — Task definitions
- `80-99*.mk` — Hook implementations

**Why This Matters:**

- **Maintainability** — Core logic separate from customizations
- **Synchronization** — Core files can be updated without losing customizations
- **Extensibility** — Add features without modifying core files

**Example Flow:**

```
make test
  ↓
Makefile (includes .rhiza/rhiza.mk)
  ↓
.rhiza/rhiza.mk:test target
  ↓
pre-test:: hooks (from .rhiza/make.d/80-*.mk)
  ↓
uv run pytest
  ↓
post-test:: hooks (from .rhiza/make.d/85-*.mk)
```

---

### Template Synchronization Mechanism

**How Sync Works:**

```mermaid
sequenceDiagram
    participant W as Workflow/User
    participant M as make sync
    participant U as uvx rhiza
    participant T as Template Repo
    participant L as Local Project
    
    W->>M: make sync
    M->>U: uvx "rhiza>=X.Y.Z" materialize
    U->>T: Fetch templates
    T-->>U: Return files
    U->>U: Apply include/exclude filters
    U->>L: Update matching files
    L-->>U: Status
    U-->>M: Complete
    M-->>W: Done
```

**Configuration Flow:**

1. **Read `.rhiza/template.yml`:**
   ```yaml
   repository: Jebel-Quant/rhiza
   ref: main
   include: |
     .github/workflows/*.yml
   exclude: |
     local.mk
   ```

2. **Fetch from upstream** — Clone/pull template repository

3. **Filter files:**
   - Apply `include` patterns (whitelist)
   - Apply `exclude` patterns (blacklist)
   - Result: Only matched files are considered

4. **Update local project:**
   - Copy matched files to project
   - Preserve excluded files
   - Report changes

**Key Insight:** The `exclude` list protects your customizations from being overwritten.

---

### CI/CD Pipeline Architecture

**Workflow Dependencies:**

```mermaid
graph TD
    A[Generate Matrix] --> B[Test Python 3.11]
    A --> C[Test Python 3.12]
    A --> D[Test Python 3.13]
    A --> E[Test Python 3.14]
    
    B --> F[Security Scan]
    C --> F
    D --> F
    E --> F
    
    F --> G[Type Check]
    G --> H[Dependency Check]
    H --> I[Validate]
    
    I --> J{On main?}
    J -->|Yes| K[Build Docs]
    J -->|No| L[Skip]
    
    K --> M[Deploy Pages]
    
    style A fill:#2fa4a9
    style M fill:#4ade80
```

**Matrix Generation:**

The CI matrix is dynamically generated from `pyproject.toml`:

```python
# .rhiza/utils/version_matrix.py
def get_python_versions():
    classifiers = parse_pyproject()["classifiers"]
    versions = extract_versions(classifiers)
    return json.dumps(versions)
```

**Why Dynamic?**

- No manual updates needed
- Single source of truth (`pyproject.toml`)
- Prevents version drift between docs and CI

---

### Dependency Management Architecture

**uv Lock File Flow:**

```mermaid
flowchart LR
    A[pyproject.toml] -->|uv lock| B[uv.lock]
    B -->|uv sync| C[.venv/]
    
    D[uv add pkg] -->|updates| A
    D -->|updates| B
    D -->|installs| C
    
    style A fill:#ffd700
    style B fill:#87ceeb
    style C fill:#90ee90
```

**Key Files:**

1. **`pyproject.toml`** — Human-editable dependency declarations
2. **`uv.lock`** — Exact resolved dependency versions (commit this!)
3. **`.venv/`** — Actual installed packages (never commit)

**Safety Mechanisms:**

1. **Pre-commit hook** — Runs `uv lock --check` before commit
2. **CI check** — Fails if lock file out of sync
3. **Make install** — Validates lock file before proceeding

**Workflow:**

```bash
# Option 1: uv add (recommended)
uv add requests
# ✓ Updates pyproject.toml
# ✓ Updates uv.lock
# ✓ Installs to .venv

# Option 2: Manual edit (not recommended)
vim pyproject.toml  # Add requests
uv lock             # ← You must remember this!
uv sync             # ← And this!
```

---

### Hook System Deep Dive

**How Hooks Work:**

Hooks use Make's **double-colon rules** (`::`), which allow multiple definitions of the same target:

```makefile
# .rhiza/rhiza.mk
install: pre-install actual-install post-install

pre-install::
	# Empty by default

post-install::
	# Empty by default

# .rhiza/make.d/90-hooks.mk
post-install::
	@echo "Custom post-install hook"

# local.mk
post-install::
	@echo "Another post-install hook"
```

**Execution Order:**

All `post-install::` definitions run in order:
1. Default (empty)
2. From `.rhiza/make.d/90-hooks.mk`
3. From `local.mk`

**Available Hooks:**

| Hook | When It Runs | Use Case |
|------|--------------|----------|
| `pre-install` | Before dependencies install | Check system requirements |
| `post-install` | After dependencies install | Run migrations, setup config |
| `pre-sync` | Before template sync | Backup current configs |
| `post-sync` | After template sync | Apply customizations |
| `pre-validate` | Before validation | Generate code |
| `post-validate` | After validation | Additional checks |
| `pre-bump` | Before version bump | Update changelog |
| `post-bump` | After version bump | Tag dependencies |
| `pre-release` | Before release | Build artifacts |
| `post-release` | After release | Deploy, notify team |

---

### Release Process Deep Dive

**Detailed Release Flow:**

```mermaid
flowchart TD
    A[Developer: make bump] --> B[Version Incremented]
    B --> C[Developer: make release]
    C --> D[Tag Created & Pushed]
    
    D --> E[GitHub: rhiza_release.yml]
    E --> F{Validate Tag}
    F -->|Invalid| G[❌ Fail]
    F -->|Valid| H{Build System?}
    
    H -->|Has pyproject.toml| I[Build with Hatch]
    H -->|No build system| J[Skip Build]
    
    I --> K[Create Draft Release]
    J --> K
    
    K --> L{Has dist/?}
    L -->|Yes| M{Private Package?}
    L -->|No| N[Skip PyPI]
    
    M -->|No| O[Publish to PyPI]
    M -->|Yes| N
    
    K --> P{PUBLISH_DEVCONTAINER?}
    P -->|true| Q[Build & Push Container]
    P -->|false| R[Skip Container]
    
    O --> S[Finalize Release]
    Q --> S
    N --> S
    R --> S
    
    S --> T[✅ Release Published]
    
    style A fill:#2fa4a9
    style T fill:#4ade80
    style G fill:#ff6b6b
```

**SLSA Provenance:**

For public repositories, GitHub automatically generates **SLSA provenance attestations**:

- Cryptographic proof of build process
- Links artifacts to source code
- Verifiable build transparency

**Trusted Publishing:**

Instead of storing PyPI tokens:

1. Register your repo as a **Trusted Publisher** on PyPI
2. PyPI issues short-lived OIDC tokens to GitHub Actions
3. No long-lived credentials stored

---

### Security Scanning Architecture

**Multi-Layer Security:**

```mermaid
flowchart TD
    A[Code Push] --> B[Pre-commit]
    B --> C{Passes?}
    C -->|No| D[❌ Block Commit]
    C -->|Yes| E[Push to GitHub]
    
    E --> F[Security Workflow]
    F --> G[pip-audit]
    F --> H[bandit]
    F --> I[mypy]
    
    G --> J{Vulnerabilities?}
    H --> J
    I --> J
    
    J -->|Yes| K[❌ Fail CI]
    J -->|No| L[CodeQL Optional]
    
    L --> M{Advanced Security?}
    M -->|Yes| N[Deep Analysis]
    M -->|No| O[Skip]
    
    N --> P{Issues?}
    P -->|Yes| Q[❌ Alert]
    P -->|No| R[✅ Pass]
    
    style D fill:#ff6b6b
    style K fill:#ff6b6b
    style Q fill:#ff6b6b
    style R fill:#4ade80
```

**Scanning Tools:**

1. **pip-audit** — CVE database check for dependencies
2. **bandit** — Static analysis for common Python security issues
3. **mypy** — Type safety (prevents certain bug classes)
4. **CodeQL** — Advanced semantic analysis (requires GitHub Advanced Security)

**Why Multiple Tools?**

Each catches different issue types:

- **pip-audit**: Known vulnerabilities in third-party packages
- **bandit**: Hardcoded passwords, SQL injection, etc.
- **mypy**: Type errors that could cause runtime issues
- **CodeQL**: Complex dataflow analysis (e.g., taint tracking)

---

## Design Principles

### 1. Convention Over Configuration

Rhiza provides sensible defaults so you can start immediately:

- Python 3.11+ (modern)
- pytest for testing
- ruff for linting
- uv for dependency management

**Override when needed**, but defaults work for 90% of projects.

---

### 2. Separation of Concerns

Clear boundaries between components:

| Component | Responsibility | Synced? |
|-----------|----------------|---------|
| `.rhiza/` | Core Rhiza logic | ✅ Yes |
| `local.mk` | Project-specific overrides | ❌ No |
| `src/` | Application code | ❌ No |
| `tests/` | Test suite | ❌ No |
| `.github/workflows/` | CI/CD | ✅ Yes (optional) |

---

### 3. Fail Fast

Errors detected early:

- **Pre-commit hooks** — Before code reaches CI
- **Lock file checks** — Before tests run
- **Type checking** — Before deployment
- **Security scans** — On every push

---

### 4. Reproducibility

Exact reproduction of environments:

- `uv.lock` pins all dependency versions
- Docker containers with fixed base images
- Python version matrix in CI
- Platform-specific lock files (if needed)

---

### 5. Transparency

No magic:

- All scripts in `.rhiza/scripts/` (bash, readable)
- All logic in `.rhiza/rhiza.mk` (make, readable)
- All workflows in `.github/workflows/` (YAML, readable)
- No binary blobs, no hidden behavior

---

## Performance Characteristics

### uv vs pip

**Speed Comparison:**

| Operation | pip | uv | Speedup |
|-----------|-----|----|----|
| Cold install | 45s | 1.2s | **37x** |
| Warm install | 30s | 0.8s | **37x** |
| Lock file generation | 15s | 0.5s | **30x** |

**Why uv is faster:**

- Written in Rust (compiled, not interpreted)
- Parallel dependency resolution
- Efficient caching
- Minimal network requests

---

### CI Optimization

**Parallel Execution:**

```yaml
jobs:
  test:
    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13", "3.14"]
    # All versions run in parallel
```

**Caching:**

```yaml
- name: Cache uv
  uses: actions/cache@v4
  with:
    path: ~/.cache/uv
```

Typical time savings: **3-5 minutes per run**

---

## Related Documentation

- [Workflows](WORKFLOWS.md) — Day-to-day development
- [Customization](CUSTOMIZATION.md) — Extending Rhiza
- [CI/CD](ci-cd.md) — Workflow details
- [Quick Reference](QUICK_REFERENCE.md) — Command cheat sheet
- [Glossary](GLOSSARY.md) — Term definitions
