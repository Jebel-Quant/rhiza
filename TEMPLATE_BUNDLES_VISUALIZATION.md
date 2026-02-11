# Rhiza Template Bundle Visualization

Visual diagrams illustrating the template bundle system design.

---

## Bundle Dependency Graph

```mermaid
graph TD
    core[core - Required<br/>~30 files]
    tests[tests<br/>~30 files]
    docker[docker<br/>~5 files]
    marimo[marimo<br/>~6 files]
    book[book<br/>~5 files]
    devcontainer[devcontainer<br/>~4 files]
    gitlab[gitlab<br/>~15 files]
    presentation[presentation<br/>~2 files]
    
    core -.->|always included| tests
    core -.->|always included| docker
    core -.->|always included| marimo
    core -.->|always included| book
    core -.->|always included| devcontainer
    core -.->|always included| gitlab
    core -.->|always included| presentation
    
    book -->|requires| tests
    book -.->|recommends| marimo
    
    style core fill:#e1f5e1,stroke:#4caf50,stroke-width:3px
    style book fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style tests fill:#d1ecf1,stroke:#0dcaf0,stroke-width:2px
    style marimo fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style docker fill:#cfe2ff,stroke:#0d6efd,stroke-width:2px
    style devcontainer fill:#e7e7ff,stroke:#6610f2,stroke-width:2px
    style gitlab fill:#ffeeba,stroke:#fd7e14,stroke-width:2px
    style presentation fill:#d3d3d3,stroke:#6c757d,stroke-width:2px
```

**Legend:**
- 🟢 Green: Required (core)
- 🟡 Yellow: Composite bundle (has dependencies)
- 🔵 Blue: Standalone bundles
- Solid arrow: Hard requirement
- Dotted arrow: Optional recommendation

---

## Bundle File Distribution

```mermaid
pie title "File Count by Bundle (~95 total files)"
    "core" : 30
    "tests" : 30
    "gitlab" : 15
    "marimo" : 6
    "docker" : 5
    "book" : 5
    "devcontainer" : 4
    "presentation" : 2
```

---

## Template Resolution Flow

```mermaid
flowchart TD
    user[User Config<br/>.rhiza/template.yml] --> parse[Parse Configuration]
    parse --> has_templates{Has templates<br/>field?}
    
    has_templates -->|Yes| fetch[Fetch Bundle Definitions<br/>from upstream repo]
    fetch --> resolve[Resolve Templates<br/>to File Lists]
    resolve --> deps[Auto-include<br/>Dependencies]
    deps --> merge[Merge with include<br/>patterns]
    
    has_templates -->|No| legacy[Use include<br/>patterns only]
    legacy --> merge
    
    merge --> exclude[Apply exclude<br/>patterns]
    exclude --> materialize[Materialize<br/>Files]
    
    style user fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    style fetch fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style materialize fill:#d1ecf1,stroke:#0dcaf0,stroke-width:2px
```

---

## Bundle Composition by Feature

```mermaid
graph LR
    subgraph docker[Docker Bundle]
        d1[docker/Dockerfile]
        d2[.rhiza/make.d/07-docker.mk]
        d3[.github/workflows/rhiza_docker.yml]
        d4[docs/DOCKER.md]
    end
    
    subgraph tests[Tests Bundle]
        t1[pytest.ini]
        t2[.rhiza/make.d/01-test.mk]
        t3[tests/**]
        t4[.github/workflows/rhiza_ci.yml]
        t5[.github/workflows/rhiza_benchmarks.yml]
        t6[+ 5 more workflows]
    end
    
    subgraph book[Book Bundle]
        b1[.rhiza/make.d/02-book.mk]
        b2[.rhiza/templates/minibook/**]
        b3[.github/workflows/rhiza_book.yml]
        b4[docs/BOOK.md]
        b5[requires: tests]
    end
    
    subgraph marimo[Marimo Bundle]
        m1[book/marimo/**]
        m2[.rhiza/make.d/03-marimo.mk]
        m3[.github/workflows/rhiza_marimo.yml]
        m4[docs/MARIMO.md]
    end
```

---

## User Configuration Evolution

### Before: Manual File Listing

```mermaid
flowchart LR
    user[User] -->|manually lists| files[docker/Dockerfile<br/>.rhiza/make.d/07-docker.mk<br/>.github/workflows/rhiza_docker.yml<br/>docs/DOCKER.md]
    files -->|risk of<br/>missing files| incomplete[Incomplete<br/>Setup]
    
    style incomplete fill:#f8d7da,stroke:#dc3545,stroke-width:2px
```

### After: Template Selection

```mermaid
flowchart LR
    user[User] -->|selects| template[templates:<br/>- docker]
    template -->|automatically<br/>includes all| files[docker/Dockerfile<br/>.rhiza/make.d/07-docker.mk<br/>.github/workflows/rhiza_docker.yml<br/>docs/DOCKER.md<br/>+ any future files]
    files -->|guaranteed<br/>complete| complete[Complete<br/>Setup]
    
    style complete fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
```

---

## Example: Data Science Project Setup

```mermaid
flowchart TD
    config["User selects:<br/>templates:<br/>  - tests<br/>  - marimo<br/>  - book"]
    
    config --> expand[Expand Templates]
    
    expand --> core_auto[AUTO: core<br/>~30 files]
    expand --> tests_user[USER: tests<br/>~30 files]
    expand --> marimo_user[USER: marimo<br/>~6 files]
    expand --> book_user[USER: book<br/>~5 files]
    
    book_user -.->|requires| tests_dep[AUTO: tests<br/>already selected ✓]
    book_user -.->|recommends| marimo_dep[AUTO: marimo<br/>already selected ✓]
    
    core_auto --> total[Total: ~71 files]
    tests_user --> total
    marimo_user --> total
    book_user --> total
    
    style config fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    style total fill:#d1ecf1,stroke:#0dcaf0,stroke-width:3px
    style tests_dep fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style marimo_dep fill:#fff3cd,stroke:#ffc107,stroke-width:2px
```

---

## Bundle File Breakdown

### Docker Bundle Structure

```
docker (5 files)
│
├── Configuration
│   └── docker/Dockerfile
│   └── docker/Dockerfile.dockerignore
│
├── Make Targets
│   └── .rhiza/make.d/07-docker.mk
│       ├── docker-build
│       ├── docker-run
│       └── docker-clean
│
├── CI/CD
│   └── .github/workflows/rhiza_docker.yml
│       ├── Lint with hadolint
│       └── Build validation
│
└── Documentation
    └── docs/DOCKER.md
```

### Tests Bundle Structure

```
tests (~30 files)
│
├── Configuration
│   ├── pytest.ini
│   └── .rhiza/requirements/tests.txt
│
├── Make Targets
│   └── .rhiza/make.d/01-test.mk
│       ├── test
│       ├── coverage
│       └── benchmarks
│
├── Test Suite
│   └── tests/test_rhiza/**
│       ├── conftest.py
│       ├── test_*.py (10+ files)
│       └── benchmarks/**
│
├── GitHub Actions
│   ├── .github/workflows/rhiza_ci.yml
│   ├── .github/workflows/rhiza_benchmarks.yml
│   ├── .github/workflows/rhiza_mypy.yml
│   ├── .github/workflows/rhiza_security.yml
│   └── .github/workflows/rhiza_codeql.yml
│
└── GitLab CI
    └── .gitlab/workflows/rhiza_ci.yml
```

### Book Bundle Structure

```
book (5 files + dependencies)
│
├── Configuration
│   └── .rhiza/templates/minibook/**
│
├── Make Targets
│   └── .rhiza/make.d/02-book.mk
│       └── book (aggregates: docs + coverage + tests + notebooks)
│
├── CI/CD
│   ├── .github/workflows/rhiza_book.yml (GitHub Pages)
│   └── .gitlab/workflows/rhiza_book.yml (GitLab Pages)
│
├── Documentation
│   └── docs/BOOK.md
│
└── Dependencies (auto-included)
    ├── REQUIRED: tests (for coverage & test reports)
    └── RECOMMENDED: marimo (for notebook exports)
```

---

## Migration Path

```mermaid
flowchart LR
    old[Old Config<br/>Path-based<br/>include patterns]
    
    hybrid[Hybrid Config<br/>Templates + Paths<br/>both work]
    
    new[New Config<br/>Template-based<br/>clean & simple]
    
    old -->|Phase 1<br/>Add templates| hybrid
    hybrid -->|Phase 2<br/>Remove redundant<br/>include patterns| new
    
    style old fill:#f8d7da,stroke:#dc3545,stroke-width:2px
    style hybrid fill:#fff3cd,stroke:#ffc107,stroke-width:2px
    style new fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
```

**Example Migration:**

```yaml
# Phase 1: Old Config (before)
include: |
  docker/Dockerfile
  docker/Dockerfile.dockerignore
  .rhiza/make.d/07-docker.mk
  .github/workflows/rhiza_docker.yml
  docs/DOCKER.md
  pytest.ini
  .rhiza/make.d/01-test.mk
  tests/**
  .github/workflows/rhiza_ci.yml
  # ... many more lines ...

# Phase 2: Hybrid (during migration)
templates:
  - docker
  - tests

include: |
  scripts/custom-deploy.sh  # Custom files only

# Phase 3: New Config (after)
templates:
  - docker
  - tests
  - book

exclude: |
  tests/benchmarks/**  # Optional exclusions
```

---

## Bundle Versioning

```mermaid
flowchart TD
    v1[Bundle Schema v1.0<br/>Initial Release]
    v1_1[Bundle Schema v1.1<br/>Add new bundles]
    v2[Bundle Schema v2.0<br/>Breaking changes]
    
    v1 -->|backward compatible| v1_1
    v1_1 -->|major version bump| v2
    
    cli_old[rhiza-cli 0.x] -.->|supports| v1
    cli_new[rhiza-cli 1.x] -.->|supports| v1
    cli_new -.->|supports| v1_1
    cli_future[rhiza-cli 2.x] -.->|supports| v2
    
    style v1 fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    style v1_1 fill:#d1ecf1,stroke:#0dcaf0,stroke-width:2px
    style v2 fill:#fff3cd,stroke:#ffc107,stroke-width:2px
```

---

## Comparison: Before vs After

| Aspect | Before (Path-based) | After (Template-based) |
|--------|---------------------|------------------------|
| **Configuration** | List 5+ files for docker | `templates: [docker]` |
| **Completeness** | User might miss files | Guaranteed complete |
| **Dependencies** | Manual (must know book needs tests) | Automatic resolution |
| **Discovery** | Read docs to find files | `uvx rhiza list-templates` |
| **Maintenance** | Update config when files added | Automatic (bundle evolves) |
| **Customization** | Full control, verbose | Templates + include/exclude |
| **Learning Curve** | Must know all file paths | Select features |

---

## Implementation Timeline

```mermaid
gantt
    title Template Bundle System Implementation
    dateFormat  YYYY-MM-DD
    section Definition
    Create bundle definitions           :done, 2025-02-04, 1d
    Document design                     :done, 2025-02-04, 1d
    Update repository analysis          :done, 2025-02-04, 1d
    
    section Implementation
    rhiza-cli: Add templates field      :active, 2025-02-05, 3d
    rhiza-cli: Bundle resolution        :2025-02-08, 3d
    rhiza-cli: Dependency resolution    :2025-02-11, 2d
    rhiza-cli: list-templates command   :2025-02-13, 1d
    
    section Testing
    Unit tests                          :2025-02-14, 2d
    Integration tests                   :2025-02-16, 2d
    Manual testing                      :2025-02-18, 1d
    
    section Documentation
    Update README                       :2025-02-19, 1d
    Update CUSTOMIZATION                :2025-02-20, 1d
    Update rhiza-cli docs              :2025-02-21, 1d
    
    section Release
    Code review                         :2025-02-22, 1d
    Release v0.X.0                     :milestone, 2025-02-23, 0d
```

---

*This visualization document complements the technical design in `TEMPLATE_BUNDLES_DESIGN.md`*
