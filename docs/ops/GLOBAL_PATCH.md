# Global Patch Workflow

When the same change must be propagated across multiple bundles, treat it as a
single "global patch" and apply it consistently bundle-by-bundle.

This workflow is useful for changes such as:

- adopting a new tool across all relevant bundles
- updating the same workflow stub in multiple overlays
- changing a configuration file that several bundles own at the same relative path —
  `.pre-commit-config.yaml` in each of the three language layers, `.bumpversion.toml` in
  two of them

## Workflow

1. **Identify the shared file path**

   Work with the file's path relative to a bundle root, then list every bundle
   that owns that path.

   ```bash
   FILE=.pre-commit-config.yaml
   find bundles -path "*/${FILE}" | sort
   ```

2. **Edit every matching bundle copy**

   Apply the same semantic change to each matching file under
   `bundles/<bundle>/...`.

   For repository-wide refactors, keep the relative path identical in every
   bundle so the change remains easy to review and validate.

3. **Diff the repeated file across bundles**

   Before committing, compare the same file across all matching bundles to spot
   drift or missed edits. If you do not have a dedicated helper target yet, this
   small helper script compares every match against the first bundle copy:

   ```bash
   FILE=.pre-commit-config.yaml
   python - <<'PY' "$FILE"
   from pathlib import Path
   import difflib
   import sys

   target = sys.argv[1]
   paths = sorted(Path("bundles").glob(f"*/{target}"))
   if len(paths) < 2:
       raise SystemExit(f"Need at least two bundle files for {target!r}")

   def bundle_name(path: Path) -> str:
       return path.relative_to("bundles").parts[0]

   baseline = paths[0]
   baseline_lines = baseline.read_text().splitlines()

   for path in paths[1:]:
       print(f"\n=== {bundle_name(baseline)} vs {bundle_name(path)} ===")
       diff = difflib.unified_diff(
           baseline_lines,
           path.read_text().splitlines(),
           fromfile=str(baseline),
           tofile=str(path),
           lineterm="",
       )
       output = "\n".join(diff)
       print(output or "(no differences)")
   PY
   ```

   If you later want a reusable shortcut, wrap the same pattern in a local
   helper script, since no make target does this.

4. **Run validation**

   After editing all bundle copies, run:

   ```bash
   make test          # the bundle contract: tests/bundles/
   make sync-self-check   # dogfood symlinks, if you added a bundle file
   ```

   `make test` is the one that matters here: `tests/bundles/` asserts the bundle contract,
   including the copies that cannot be symlinks and are kept in step by a test instead
   (`test_bundle_github_sync.py`, `test_bundle_rhiza_sync.py`). `make rhiza-test` is a
   different gate — it runs pytest-rhiza's checks *about a repository*, and knows nothing
   about bundle-to-bundle drift.

## Review Checklist

- [ ] every intended bundle file was updated
- [ ] the relative path is still identical across bundles
- [ ] bundle-to-bundle diffs only show the intended change
- [ ] `make test` passes from the repository root
