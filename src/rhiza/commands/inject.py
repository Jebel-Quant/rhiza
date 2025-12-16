"""Command-line helpers for working with Rhiza templates.

This module currently exposes a thin wrapper that shells out to the
`tools/inject_rhiza.sh` script. It exists so the functionality can be
invoked via a Python entry point while delegating the heavy lifting to
the maintained shell script.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from loguru import logger


def expand_paths(base_dir: Path, paths: list[str]) -> list[Path]:
    """Expand files/directories relative to base_dir into a flat list of files.

    Given a list of paths relative to ``base_dir``, return a flat list of all
    individual files.
    """
    all_files = []
    for p in paths:
        full_path = base_dir / p
        if full_path.is_file():
            all_files.append(full_path)
        elif full_path.is_dir():
            all_files.extend([f for f in full_path.rglob("*") if f.is_file()])
        else:
            # Path does not exist — could log a warning
            continue
    return all_files


def inject(target: Path, branch: str, force: bool):
    """Materialize rhiza templates into TARGET repository."""
    # Convert to absolute path to avoid surprises
    target = target.resolve()

    # Validate target is a git repository
    if not (target / ".git").is_dir():
        logger.error(f"Target directory is not a git repository: {target}")
        raise sys.exit(1)

    logger.info(f"Target repository: {target}")
    logger.info(f"Rhiza branch: {branch}")

    # -----------------------
    # Ensure template.yml
    # -----------------------
    template_file = target / ".github" / "template.yml"
    template_file.parent.mkdir(parents=True, exist_ok=True)

    if not template_file.exists():
        logger.info("Creating default .github/template.yml")
        template_content = {
            "template-repository": "jebel-quant/rhiza",
            "template-branch": branch,
            "include": [
                ".github",
                ".editorconfig",
                ".gitignore",
                ".pre-commit-config.yaml",
                "Makefile",
                "pytest.ini",
            ],
        }
        with open(template_file, "w") as f:
            yaml.dump(template_content, f)
        logger.success(".github/template.yml created")
    else:
        logger.info("Using existing .github/template.yml")

    # -----------------------
    # Load template.yml
    # -----------------------
    with open(template_file) as f:
        config = yaml.safe_load(f)

    rhiza_repo = config.get("template-repository")
    rhiza_branch = config.get("template-branch", branch)
    include_paths = config.get("include", [])
    excluded_paths = config.get("exclude", [])

    if not include_paths:
        logger.error("No include paths found in template.yml")
        raise sys.exit(1)

    logger.info("Include paths:")
    for p in include_paths:
        logger.info(f"  - {p}")

    # -----------------------
    # Sparse clone rhiza
    # -----------------------
    tmp_dir = Path(tempfile.mkdtemp())
    logger.info(f"Cloning {rhiza_repo}@{rhiza_branch} into temporary directory")

    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--filter=blob:none",
                "--sparse",
                "--branch",
                rhiza_branch,
                f"https://github.com/{rhiza_repo}.git",
                str(tmp_dir),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )

        subprocess.run(["git", "sparse-checkout", "init"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "sparse-checkout", "set", "--skip-checks", *include_paths], cwd=tmp_dir, check=True)

        # After sparse-checkout
        all_files = expand_paths(tmp_dir, include_paths)

        # Filter out excluded files
        # excluded_set = {tmp_dir / e for e in excluded_paths}
        excluded_files = expand_paths(tmp_dir, excluded_paths)

        files_to_copy = [f for f in all_files if f not in excluded_files]
        # print(files_to_copy)

        # Copy loop
        for src_file in files_to_copy:
            dst_file = target / src_file.relative_to(tmp_dir)
            if dst_file.exists() and not force:
                logger.warning(f"{dst_file.relative_to(target)} already exists — use force=True to overwrite")
                continue

            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
            logger.success(f"[ADD] {dst_file.relative_to(target)}")

    finally:
        shutil.rmtree(tmp_dir)

    logger.success("Rhiza templates materialized successfully")
    logger.info("""
Next steps:
  1. Review changes:
       git status
       git diff

  2. Commit:
       git add .
       git commit -m "chore: import rhiza templates"

This is a one-shot snapshot.
Re-run this script to update templates explicitly.
""")
