---
description: Cut a release — preview the version bump, push the tag, and watch the release workflow
allowed-tools: Bash, Read
---

Cut a release for this repository. Follow the command-execution policy: always
prefer `make <target>`; never invoke `.venv/bin/...` directly.

How releasing works here. `make release` delegates to `rhiza-tools release`
(`.rhiza/make.d/releasing.mk`). It **always bumps** the version, folds a freshly
generated `CHANGELOG.md` into the version-bump commit (git-cliff pre-commit
hook), creates a `v*` tag, and pushes it. The tag push triggers the
`rhiza_release.yml` GitHub Actions workflow (validate → build → SBOM → draft →
publish → finalize). There is no separate post-tag changelog commit — the tagged
commit already carries the changelog.

Do the following, in order:

1. **Pre-flight checks.** Confirm the release is safe to cut and stop with a
   clear explanation if any check fails (do not push a tag from a dirty or
   behind branch):
   - Working tree is clean (`git status --porcelain` is empty).
   - On the default branch (`main`) — or confirm with the user if not.
   - Local `main` is up to date with `origin/main` (`git fetch` then compare).
   - `pyproject.toml` exists (the bump is skipped without it).

2. **Preview the bump (dry run).** Run `make release DRY_RUN=1` and show the
   user the planned new version and tag **before** anything is pushed. The
   `DRY_RUN=1` flag previews the bump/tag/push without applying them. Summarise
   what the real run will do (old → new version, tag name).

3. **Confirm.** Unless `$ARGUMENTS` explicitly authorises proceeding (see
   below), stop here and ask the user to confirm the previewed version before
   cutting the real release. Pushing a tag triggers a public release workflow —
   treat it as outward-facing and confirm first.

4. **Cut the release.** Run `make release`. This bumps, commits (with changelog),
   tags, and pushes. Run it in the foreground so any failure is visible. If it
   fails, show the relevant output, diagnose the root cause, and stop — do not
   re-run blindly or hand-craft a tag.

5. **Watch the workflow.** Run `make release-status` to show the release
   workflow run and the latest release info. If the workflow is still in
   progress, tell the user it is running and how to re-check
   (`make release-status`). Report the final release URL once available.

6. **Report.** Tell the user the version that was released, the tag, and the
   release/workflow URL. If anything is still pending (workflow running, draft
   not yet published), say so plainly.

`$ARGUMENTS` handling:

- Empty → run the full preview-then-confirm flow above.
- `dry-run` (or `preview`) → do steps 1–2 only and stop; do **not** cut a real
  release.
- `yes` / `confirm` / `--force` → skip the interactive confirmation in step 3
  and proceed straight through (still run the dry-run preview in step 2 so the
  user sees what shipped).
- `status` → skip to step 5 and just report current release/workflow status.
