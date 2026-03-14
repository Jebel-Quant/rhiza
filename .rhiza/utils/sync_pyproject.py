"""Sync selected pyproject.toml fields from .rhiza/template.yml.

This file flows down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Non-destructively patches the project's pyproject.toml with values declared in
the ``pyproject:`` section of ``.rhiza/template.yml``.  All project-specific
fields (``name``, ``version``, ``description``, ``authors``, ``keywords``,
``dependencies``, ``[dependency-groups]``, ``[project.urls]``) are never
touched unless they are explicitly listed in the template.

Supported ``pyproject:`` keys in template.yml
---------------------------------------------
requires-python
    Sets ``[project].requires-python``.
classifiers
    Replaces ``[project].classifiers`` entirely (rhiza owns this list).
license
    Sets ``[project].license``.  Accepts either a plain string (PEP 639,
    e.g. ``"MIT"``) or a mapping (PEP 517, e.g. ``{text: "MIT"}`` or
    ``{file: "LICENSE"}``).
readme
    Sets ``[project].readme`` (a string file path, e.g. ``"README.md"``).
tool-sections
    A list of dotted TOML paths (e.g. ``tool.deptry.package_module_name_map``)
    that are synced wholesale from rhiza's own ``pyproject.toml`` into the
    downstream project's ``pyproject.toml``.

Usage
-----
    uv run python .rhiza/utils/sync_pyproject.py [--dry-run] [--check]

Flags
-----
--dry-run   Preview changes without writing.
--check     Exit non-zero if changes would be made (useful in CI).

Security Notes
--------------
- S603 (subprocess without shell=True): Not used in this module.
- No external network calls are made.
"""

from __future__ import annotations

import argparse
import difflib
import sys
import textwrap
import tomllib
from pathlib import Path

import tomlkit
import yaml  # pyyaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_paths() -> tuple[Path, Path, Path]:
    """Return (repo_root, template_yml, pyproject_toml) paths."""
    # Walk up from this script's location to find the repo root (contains pyproject.toml)
    script_dir = Path(__file__).resolve().parent
    # This script lives at .rhiza/utils/sync_pyproject.py
    # So repo root is two levels up
    repo_root = script_dir.parent.parent
    template_yml = repo_root / ".rhiza" / "template.yml"
    pyproject_toml = repo_root / "pyproject.toml"
    return repo_root, template_yml, pyproject_toml


def _load_template_yml(template_yml: Path) -> dict:
    """Load and return parsed .rhiza/template.yml."""
    with template_yml.open() as f:
        return yaml.safe_load(f) or {}


def _load_pyproject(pyproject_toml: Path) -> tomlkit.TOMLDocument:
    """Load pyproject.toml preserving formatting via tomlkit."""
    with pyproject_toml.open("rb") as f:
        return tomlkit.load(f)


def _get_nested(doc: dict, dotted_path: str):
    """Retrieve a value from a nested dict using a dotted path string.

    Returns ``None`` if any key in the path is missing.
    """
    parts = dotted_path.split(".")
    current = doc
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _set_nested(doc: tomlkit.TOMLDocument, dotted_path: str, value) -> None:
    """Set a value in a tomlkit document at the given dotted path.

    Intermediate tables are created as needed using ``tomlkit.table()``.
    """
    parts = dotted_path.split(".")
    current = doc
    for part in parts[:-1]:
        if part not in current:
            current.add(part, tomlkit.table())  # type: ignore[arg-type]
        current = current[part]
    current[parts[-1]] = value


def _tomlkit_from_raw(value) -> object:
    """Convert a plain Python value into the appropriate tomlkit type."""
    if isinstance(value, list):
        arr = tomlkit.array()
        arr.multiline(True)
        for item in value:
            arr.append(item)
        return arr
    if isinstance(value, dict):
        tbl = tomlkit.table()
        for k, v in value.items():
            tbl.add(k, _tomlkit_from_raw(v))
        return tbl
    return value


# ---------------------------------------------------------------------------
# Core patching logic
# ---------------------------------------------------------------------------


def _apply_pyproject_section(
    pyproject_doc: tomlkit.TOMLDocument,
    pyproject_section: dict,
    rhiza_pyproject: dict | None,
) -> list[str]:
    """Apply the ``pyproject:`` template section to *pyproject_doc* in-place.

    Returns a list of human-readable change descriptions.
    """
    changes: list[str] = []

    # Ensure [project] table exists
    if "project" not in pyproject_doc:
        pyproject_doc.add("project", tomlkit.table())

    project = pyproject_doc["project"]

    # --- requires-python ---
    if "requires-python" in pyproject_section:
        new_val: str = str(pyproject_section["requires-python"])
        old_val = project.get("requires-python")
        if old_val != new_val:
            project["requires-python"] = new_val
            changes.append(f"  requires-python: {old_val!r} → {new_val!r}")

    # --- classifiers ---
    if "classifiers" in pyproject_section:
        new_classifiers: list[str] = list(pyproject_section["classifiers"])
        old_classifiers = list(project.get("classifiers") or [])
        if old_classifiers != new_classifiers:
            arr = tomlkit.array()
            arr.multiline(True)
            for c in new_classifiers:
                arr.append(c)
            project["classifiers"] = arr
            changes.append("  classifiers: replaced list")

    # --- license ---
    if "license" in pyproject_section:
        new_license = pyproject_section["license"]
        old_license = project.get("license")
        # Normalise for comparison: tomlkit inline tables compare as dicts
        old_license_cmp = dict(old_license) if hasattr(old_license, "items") else old_license
        new_license_cmp = dict(new_license) if isinstance(new_license, dict) else new_license
        if old_license_cmp != new_license_cmp:
            if isinstance(new_license, dict):
                tbl = tomlkit.inline_table()
                for k, v in new_license.items():
                    tbl.append(k, v)
                project["license"] = tbl
            else:
                project["license"] = str(new_license)
            changes.append(f"  license: {old_license!r} → {new_license!r}")

    # --- readme ---
    if "readme" in pyproject_section:
        new_readme: str = str(pyproject_section["readme"])
        old_readme = project.get("readme")
        if old_readme != new_readme:
            project["readme"] = new_readme
            changes.append(f"  readme: {old_readme!r} → {new_readme!r}")

    # --- tool-sections ---
    if "tool-sections" in pyproject_section:
        if rhiza_pyproject is None:
            print("[WARN] tool-sections specified but rhiza pyproject.toml not found — skipping.")
        else:
            for dotted_path in pyproject_section["tool-sections"]:
                rhiza_val = _get_nested(rhiza_pyproject, dotted_path)
                if rhiza_val is None:
                    print(f"[WARN] tool-section '{dotted_path}' not found in rhiza pyproject.toml — skipping.")
                    continue
                current_val = _get_nested(dict(pyproject_doc), dotted_path)
                if current_val != rhiza_val:
                    _set_nested(pyproject_doc, dotted_path, _tomlkit_from_raw(rhiza_val))
                    changes.append(f"  tool-section '{dotted_path}': updated")

    return changes


# ---------------------------------------------------------------------------
# Rhiza pyproject loader (for tool-sections)
# ---------------------------------------------------------------------------


def _load_rhiza_pyproject(repo_root: Path) -> dict | None:
    """Load rhiza's own pyproject.toml for ``tool-sections`` resolution.

    Walks up the directory tree looking for a rhiza pyproject.toml located
    relative to a ``.rhiza/utils`` directory.  If unavailable, returns None.
    """
    # This script lives at <repo>/.rhiza/utils/sync_pyproject.py
    # When running in a downstream project, rhiza files are not present as a
    # separate checkout.  The ``tool-sections`` values come from rhiza's own
    # pyproject.toml (which lives at the root of *this* repo).
    # When this script runs inside the rhiza repo itself, that file is the
    # repo root pyproject.toml — i.e. the same file we are patching.
    # For downstream projects, the rhiza pyproject.toml is not available
    # on disk unless it was explicitly placed there.  We therefore look in
    # the same repo root first (covers both the rhiza repo and the common
    # case where the user has copied the script together with pyproject.toml).
    candidate = repo_root / "pyproject.toml"
    if candidate.exists():
        try:
            with candidate.open("rb") as f:
                return tomllib.load(f)
        except Exception:  # nosec B110 - best-effort load; failure means tool-sections are unavailable
            return None
    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for sync_pyproject.

    Returns:
    -------
    int
        0 on success / no changes needed.
        1 on error or when ``--check`` detects pending changes.
    """
    parser = argparse.ArgumentParser(
        description="Sync selected pyproject.toml fields from .rhiza/template.yml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              uv run python .rhiza/utils/sync_pyproject.py
              uv run python .rhiza/utils/sync_pyproject.py --dry-run
              uv run python .rhiza/utils/sync_pyproject.py --check
        """),
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if changes would be made")
    args = parser.parse_args(argv)

    repo_root, template_yml, pyproject_toml = _resolve_paths()

    # --- Validate required files ---
    if not template_yml.exists():
        print(f"[INFO] No .rhiza/template.yml found at {template_yml}, nothing to do.")
        return 0

    if not pyproject_toml.exists():
        print(f"[ERROR] pyproject.toml not found at {pyproject_toml}")
        return 1

    # --- Load template ---
    try:
        template_data = _load_template_yml(template_yml)
    except Exception as exc:
        print(f"[ERROR] Failed to load {template_yml}: {exc}")
        return 1

    pyproject_section = template_data.get("pyproject")
    if not pyproject_section:
        print("[INFO] No pyproject: section in template.yml, nothing to do.")
        return 0

    # --- Load pyproject.toml ---
    try:
        pyproject_doc = _load_pyproject(pyproject_toml)
    except Exception as exc:
        print(f"[ERROR] Failed to load {pyproject_toml}: {exc}")
        return 1

    original_text = pyproject_toml.read_text(encoding="utf-8")

    # --- Load rhiza pyproject for tool-sections (best-effort) ---
    rhiza_pyproject = _load_rhiza_pyproject(repo_root) if "tool-sections" in pyproject_section else None

    # --- Apply patch ---
    changes = _apply_pyproject_section(pyproject_doc, pyproject_section, rhiza_pyproject)

    if not changes:
        print("[INFO] pyproject.toml is already up to date.")
        return 0

    # --- Produce new text ---
    new_text = tomlkit.dumps(pyproject_doc)

    # --- Show diff ---
    diff = list(
        difflib.unified_diff(
            original_text.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile="pyproject.toml (before)",
            tofile="pyproject.toml (after)",
        )
    )
    print("[INFO] Changes to pyproject.toml:")
    for line in changes:
        print(line)
    print()
    if diff:
        print("--- diff ---")
        sys.stdout.writelines(diff)
        print()

    if args.check:
        print("[CHECK] pyproject.toml is NOT up to date. Run sync-pyproject to apply changes.")
        return 1

    if args.dry_run:
        print("[DRY-RUN] No changes written.")
        return 0

    # --- Write ---
    pyproject_toml.write_text(new_text, encoding="utf-8")
    print("[INFO] pyproject.toml updated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
