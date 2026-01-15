# Rhiza Project Analysis

**Date**: 2026-01-15
**Last Updated**: 2026-01-15
**Analysed by**: Claude Code (claude-opus-4-5-20251101)

---

## Executive Summary

Rhiza is a **mature, well-engineered living template system** for modern Python projects. Unlike traditional one-time templates (cookiecutter, copier), it enables continuous synchronisation of configuration and best practices across repositories.

**Overall Rating: 8.5/10**

The project demonstrates professional-grade code quality, testing infrastructure, and CI/CD. The modular Makefile system with hooks is particularly elegant. Main improvement areas: error recovery, version synchronisation, and audit logging.

---

## Strengths

### 1. Professional Build System

**Modular Makefile Architecture**
- Core logic in `.rhiza/rhiza.mk` (269 lines)
- Clean separation: `tests.mk`, `book.mk`, `docker.mk`, `github.mk`
- Entry point `Makefile` is a thin wrapper (70 lines)

**Hook System**
Double-colon rules (`::`) enable extensibility without conflicts:
```makefile
post-install::
    @echo "Custom post-install logic"
```

Available hooks: `pre/post-install`, `pre/post-sync`, `pre/post-validate`, `pre/post-release`, `pre/post-bump`

**Smart Variable Management**
- Python version sourced from `.python-version` (single source of truth)
- `UV_NO_MODIFY_PATH=1` exported to avoid PATH pollution
- Conditional venv creation only if non-existent

**Excellent Error Messages**
Colour-coded output with consistent formatting:
```
[INFO]  Installing dependencies...
[WARN]  uv and uvx already installed in ./bin, skipping.
[ERROR] Could not determine version from pyproject.toml
[SUCCESS] Release v1.0.0 complete
```

### 2. Comprehensive CI/CD

**11 GitHub Actions Workflows**

| Workflow | Purpose |
|----------|---------|
| `rhiza_ci.yml` | Multi-version Python testing (3.11-3.14) |
| `rhiza_release.yml` | Tag-triggered PyPI publishing with OIDC |
| `rhiza_sync.yml` | Template synchronisation PRs |
| `rhiza_pre-commit.yml` | Pre-commit validation |
| `rhiza_deptry.yml` | Dependency checking |
| `rhiza_validate.yml` | Project structure validation |
| `rhiza_book.yml` | Documentation building |
| `rhiza_marimo.yml` | Notebook validation |
| `rhiza_docker.yml` | Docker image building |
| `rhiza_devcontainer.yml` | Dev container validation |
| `rhiza_codeql.yml` | Security scanning |

**Security Best Practices**
- OIDC authentication for PyPI (Trusted Publishing, no stored credentials)
- Minimal permissions: `contents: read` for most workflows
- PAT_TOKEN configuration with fallback to GITHUB_TOKEN

**Smart Conditionals**
- Skips validation in rhiza repository itself
- Container image publishing only if `PUBLISH_DEVCONTAINER=true`
- PyPI publishing skipped if `Private :: Do Not Upload` classifier set

### 3. Strong Test Infrastructure

**Coverage**: 1,736 lines across 13 test files

| Test File | Purpose |
|-----------|---------|
| `conftest.py` | Fixtures: `root`, `logger`, `git_repo` |
| `test_makefile.py` | Makefile target validation |
| `test_makefile_api.py` | Makefile API tests |
| `test_release_script.py` | Release automation (236 lines) |
| `test_readme.py` | README code block execution |
| `test_notebooks.py` | Marimo notebook validation |
| `test_docstrings.py` | Docstring validation |
| `test_structure.py` | Project structure checks |
| `test_requirements_folder.py` | Requirements validation |

**Well-Designed Fixtures**
- Mock git repository with bare remotes and clones
- Mock `uv` script simulating version bumping
- Proper test isolation with `monkeypatch`

**Security-Conscious Testing**
- Uses `shutil.which()` to resolve executables (prevents S607 Bandit warnings)
- Subprocess calls properly guarded with `capture_output=True`

### 4. Security Posture

| Aspect | Implementation |
|--------|----------------|
| PyPI Authentication | OIDC (Trusted Publisher) |
| Token Management | PAT optional, GITHUB_TOKEN fallback |
| Script Standards | POSIX-compliant, `set -euo pipefail` |
| Credential Storage | None hardcoded; `.env` in `.gitignore` |
| Subprocess Safety | `shutil.which()`, `capture_output=True` |
| Security Scanning | CodeQL for Python and GitHub Actions |

### 5. Documentation Quality

**README.md** (471 lines)
- Visual hierarchy with badges and emojis
- "Why Rhiza?" section explaining living templates vs cookiecutter
- Multiple integration methods documented
- Executable code examples (tested via `test_readme.py`)

**Configuration Guides**
- `docs/CUSTOMIZATION.md` - Hook system explained
- `docs/RELEASING.md` - Release process documented
- `.rhiza/make.d/README.md` - Excellent cookbook with recipes

**Inline Documentation**
- Makefile comments explain rule purposes
- `ruff.toml` extensively documented with rule explanations
- Shell scripts have function headers and colour-coded output

### 6. Developer Experience

**One-Command Setup**
```bash
make install  # Installs uv, creates venv, installs all dependencies
```

**No Manual Activation**
Commands use `uv run` - no venv activation needed.

**Discovery**
- 40+ make targets with `make help`
- Dry-run support via `make -n`

**Debugging**
- Verbose logging in `pytest.ini`: `log_cli = true`, `log_cli_level = DEBUG`
- Dry-run mode shows what would execute

---

## Weaknesses

### Critical Issues

| Issue | Location | Impact | Risk |
|-------|----------|--------|------|
| No credential audit | Release workflow | Cannot trace who published packages | High |
| Path traversal risk | Template sync | `../` patterns not validated | Medium-High |
| No error recovery | `make install` | Failed install leaves partial state | Medium |
| No rollback mechanism | PyPI publishing | Published packages irreversible | Medium |

#### 1. No Credential Audit
The release workflow publishes to PyPI but doesn't log who triggered the release or when. Published packages are untraceable to specific actors.

#### 2. Path Traversal Risk
Template sync (`uvx rhiza materialize`) doesn't validate include/exclude patterns for directory escape sequences like `../`. Malicious template could write outside project directory.

#### 3. No Error Recovery
```makefile
# If this fails, partial venv state remains
${UV_BIN} sync || { printf "${RED}[ERROR]...${RESET}\n"; exit 1; }
```
No trap-based cleanup on failure.

#### 4. No Rollback Mechanism
Once a package is published to PyPI, it cannot be unpublished (only deleted). No draft/staging mechanism for releases.

### Medium Priority Issues

#### ~~Hard-Coded Versions Across Workflows~~ ✅ RESOLVED
~~Previously, uv version `0.9.24` was hardcoded in 6 places across 5 workflow files.~~

**Resolution**: Created `.rhiza/uv-version.txt` as single source of truth. All workflows now read version dynamically:
```yaml
- name: Get uv version
  id: uv-version
  run: echo "version=$(cat .rhiza/uv-version.txt)" >> $GITHUB_OUTPUT

- name: Install uv
  uses: astral-sh/setup-uv@v7
  with:
    version: ${{ steps.uv-version.outputs.version }}
```

#### No Conflict Resolution in Template Sync
If a user modifies a synced file, no strategy exists for handling conflicts during `uvx rhiza materialize`. The file is overwritten without warning.

#### Shell Script Edge Cases
```bash
# release.sh:142 - Fails if no upstream tracking branch
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null)
if [ -z "$UPSTREAM" ]; then
    error "No upstream tracking branch set..."
fi
```
Users with local-only branches hit confusing errors.

#### Complex Test Mocking
Mock UV script in `conftest.py` is 116 lines of embedded Python:
```python
MOCK_UV_SCRIPT = """#!/usr/bin/env python3
import sys
import re
# ... 116 lines ...
"""
```
- Difficult to maintain
- Doesn't handle pre-release versions (e.g., `1.0.0-alpha.1`)
- Regex-based version parsing is fragile

### Minor Issues

| Issue | Impact | Status |
|-------|--------|--------|
| No coverage badge | Metrics not visible to contributors | Open |
| ~~No end-to-end tests~~ | ~~Full workflow not validated~~ | ✅ Resolved |
| No ADRs | Design decisions undocumented | Open |
| No `make print-*` targets | Debugging Makefile variables difficult | Open |
| 40+ targets without search | Discovery friction | Open |
| No deprecation strategy | Breaking changes undocumented | Open |

---

## Technical Debt

### 1. Copy-Paste Configuration
Files like `pre-commit-config.yaml`, `ruff.toml`, `pytest.ini` are replicated across downstream projects with no centralised reference. Drift is inevitable.

### 2. Version Drift Risk
```
uv version: 0.9.24
Locations: 4+ workflow files
Update mechanism: Manual after Dependabot PR
```

### 3. Test Fixture Complexity
Mock scripts embedded in `conftest.py` are:
- 116 lines of Python for `uv` mock
- 6 lines for `make` mock
- Complex regex-based version parsing

### 4. Backward Compatibility Gaps
- No version field in `.rhiza/template.yml` schema
- No deprecation warnings for interface changes
- Breaking changes to `rhiza.mk` would affect all downstream projects

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Makefile lines | ~693 (across all .mk files) |
| Test lines | 1,736 |
| GitHub workflow files | 11 |
| README length | 471 lines |
| Python versions supported | 3.11, 3.12, 3.13, 3.14 |
| Make targets | 40+ |

---

## Recommendations

### Immediate (High Impact, Low Effort)

1. **Document PAT token requirement**
   Add to README Quick Start section:
   ```markdown
   > **Note**: Template sync requires a PAT token with `workflow` scope.
   > See [TOKEN_SETUP.md](.rhiza/docs/TOKEN_SETUP.md) for details.
   ```

2. **Add debugging targets**
   ```makefile
   print-%:
       @echo '$*=$($*)'
   ```

3. **Centralise uv version**
   Create `.rhiza/uv-version.txt`:
   ```
   0.9.24
   ```
   Reference in workflows:
   ```yaml
   version: ${{ file('.rhiza/uv-version.txt') }}
   ```

### Short-Term (2-4 weeks)

4. **Add error recovery**
   ```makefile
   install:
       @trap 'rm -rf .venv' ERR; \
       $(UV_BIN) sync --frozen
   ```

5. **Implement conflict detection**
   Before overwriting synced files, check for local modifications:
   ```bash
   if git diff --quiet "$file"; then
       cp "$template_file" "$file"
   else
       warn "Conflict detected in $file - skipping"
   fi
   ```

6. **Create end-to-end test**
   Test full workflow: init → materialize → install → test → release

7. **Add ADRs**
   Document key decisions:
   - Why `uv` over pip/poetry?
   - Why Makefile over task runners?
   - Why double-colon hooks?

### Medium-Term (1-3 months)

8. **Centralise CI workflow generation**
   Consider a workflow generator that produces YAML from a single source.

9. **Implement deprecation warnings**
   ```makefile
   deprecated-target:
       @echo "[WARN] 'deprecated-target' is deprecated, use 'new-target' instead"
       $(MAKE) new-target
   ```

10. **Add audit logging**
    Log release events to a file or external service:
    ```yaml
    - name: Log release
      run: |
        echo "Released ${{ github.ref_name }} by ${{ github.actor }} at $(date -u)" >> releases.log
    ```

---

## Conclusion

Rhiza is a well-engineered project that successfully addresses the "template drift" problem in Python development. The modular Makefile system, comprehensive CI/CD, and professional documentation make it an excellent choice for teams managing multiple repositories.

**Key strengths**: Extensibility, security posture, developer experience, testing coverage.

**Priority improvements**: Error recovery, conflict resolution, audit logging, version synchronisation.

The project is production-ready and demonstrates thoughtful engineering decisions throughout.
