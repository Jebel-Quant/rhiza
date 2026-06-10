# CI Performance Budgets and Caching

Last audited: 2026-05-28

## Job time budgets

| Job type | Budget |
|---|---|
| Lint / format | ≤ 5 min |
| Test matrix | ≤ 20 min |
| Security scan | ≤ 10 min |
| Docs build/check | ≤ 10 min |

These budgets are enforced directly in:
- `.github/workflows/rhiza_ci.yml` via `timeout-minutes`
- `bundles/gitlab-tests/.gitlab/workflows/rhiza_ci.yml` via `timeout`

## Cache audit (GitHub CI)

The Python test matrix uses shared cache keys so all matrix jobs reuse the same dependency cache per OS.

- `uv` cache key: `${{ runner.os }}-uv-${{ hashFiles('uv.lock') }}`
- `pre-commit` cache key: `${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}`

### Expected hit rates

- Warm runs on unchanged lock/config files: **80–95%+** cache hits
- Cold runs after lock/config changes: **0%** on first run, high hit rate on subsequent runs

### Cache TTL

GitHub Actions cache entries are subject to platform eviction; operationally treat cache retention as approximately **7 days without access**.

### Force a cold run (debugging)

Use one of the following:
1. Change `uv.lock` or `.pre-commit-config.yaml` (naturally rotates the key).
2. Temporarily append a one-off suffix to the cache key in a debug branch.
3. Delete matching cache entries from the GitHub Actions cache UI, then rerun the workflow.
