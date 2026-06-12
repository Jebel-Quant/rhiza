# OpenSSF Best Practices Badge (CII)

The OpenSSF Scorecard **CII-Best-Practices** check reads the project's badge level from the OpenSSF Best
Practices BadgeApp. Rhiza currently sits at `InProgress` (Scorecard score 2/10). Reaching **passing** raises the
check to its full score.

Unlike the other Scorecard checks, this one **cannot be fixed from the repository** — it requires a maintainer
to complete the questionnaire on the external BadgeApp. This document records the steps and maps each criterion
to the evidence that already exists in rhiza, so the questionnaire is mostly copy-paste.

## Steps (maintainer, ~30–60 min, one-time)

1. Go to <https://www.bestpractices.dev> → **Get Your Badge!** → sign in with GitHub.
2. Add (or claim) the project for `https://github.com/Jebel-Quant/rhiza`. Scorecard already detects an
   in-progress badge, so an entry likely exists — note its numeric **project id** from the URL
   (`https://www.bestpractices.dev/projects/<ID>`).
3. Work through the criteria using the evidence table below. Most are already satisfied.
4. Reach **passing** (all `MUST` criteria met).
5. Add the badge to `README.md` (ready-to-paste, fill in `<ID>`):

   ```markdown
   [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/<ID>/badge)](https://www.bestpractices.dev/projects/<ID>)
   ```

6. The Scorecard check re-reads the badge on its next run — trigger **Actions → "(RHIZA) SCORECARD" → Run
   workflow**, or wait for the weekly schedule.

## Evidence map (passing criteria → existing artifacts)

| Criterion | Evidence in rhiza |
| --- | --- |
| Project homepage / description | `README.md` |
| Free/open-source license (OSI) | `LICENSE` (MIT) |
| Version-controlled source, public | This GitHub repository |
| Release notes / changelog | `CHANGELOG.md`, GitHub Releases |
| Bug-reporting process | GitHub Issues; `SECURITY.md` for vulnerabilities |
| Vulnerability report process (private) | `SECURITY.md` |
| Build + automated test suite | `make test` (909 tests, 90% coverage gate), `rhiza_ci.yml` |
| Tests added with new functionality | Enforced via coverage gate + CI |
| Coding style / static analysis | `ruff`, `ty`, `bandit`, `interrogate` (`make fmt`) |
| Secured delivery (HTTPS) | GitHub + PyPI over HTTPS |
| Crypto / no hardcoded secrets | `detect-secrets` pre-commit hook |
| Dynamic / fuzz analysis | ClusterFuzzLite + Atheris (`fuzz/`, `rhiza_fuzzing.yml`) |
| Dependency vulnerability monitoring | Dependabot + Renovate + `pip-audit` (`make security`) |
| Contribution guide | `CONTRIBUTING.md` |
| Code review of changes | Branch-protection ruleset (`docs/ops/BRANCH_PROTECTION.md`) |
| Continuous integration | GitHub Actions + GitLab CI |
| Supply-chain hardening | SHA-pinned actions, OpenSSF Scorecard workflow |

## Related

- [`BRANCH_PROTECTION.md`](BRANCH_PROTECTION.md) — covers the Code-Review and Branch-Protection checks.
