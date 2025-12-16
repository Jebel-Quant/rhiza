# rhiza/tools/inject_rhiza.py
from pathlib import Path
import shutil
import sys
import tempfile
import subprocess
import yaml
import typer
from loguru import logger

app = typer.Typer(help="Materialize rhiza configuration templates into a git repository")

@app.command()
def inject(
    target: Path = typer.Argument(..., exists=True, file_okay=False, help="Target git repository"),
    branch: str = typer.Option("main", "--branch", "-b", help="Rhiza branch to use"),
    force: bool = typer.Option(False, "--force", "-y", help="Overwrite existing files"),
):
    """Materialize rhiza templates into TARGET repository."""
    # -----------------------
    # Validate target
    # -----------------------
    if not (target / ".git").is_dir():
        logger.error(f"Target directory is not a git repository: {target}")
        raise typer.Exit(code=1)

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
                "pytest.ini"
            ]
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

    if not include_paths:
        logger.error("No include paths found in template.yml")
        raise typer.Exit(code=1)

    logger.info("Include paths:")
    for p in include_paths:
        logger.info(f"  - {p}")

    # -----------------------
    # Sparse clone rhiza
    # -----------------------
    tmp_dir = Path(tempfile.mkdtemp())
    logger.info(f"Cloning {rhiza_repo}@{rhiza_branch} into temporary directory")

    try:
        subprocess.run([
            "git", "clone",
            "--depth", "1",
            "--filter=blob:none",
            "--sparse",
            "--branch", rhiza_branch,
            f"https://github.com/{rhiza_repo}.git",
            str(tmp_dir)
        ], check=True, stdout=subprocess.DEVNULL)

        subprocess.run(["git", "sparse-checkout", "init", "--cone"], cwd=tmp_dir, check=True)
        subprocess.run(["git", "sparse-checkout", "set", *include_paths], cwd=tmp_dir, check=True)

        # -----------------------
        # Copy files into target
        # -----------------------
        for path in include_paths:
            src = tmp_dir / path
            dst = target / path

            if not src.exists():
                logger.warning(f"{path} not found in rhiza — skipping")
                continue

            if dst.exists() and not force:
                logger.warning(f"{path} already exists — use --force to overwrite")
                continue

            if dst.exists():
                if dst.is_dir():
                    shutil.rmtree(dst)
                else:
                    dst.unlink()

            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

            logger.success(f"[ADD] {path}")

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

# -----------------------
# Entry point
# -----------------------
if __name__ == "__main__":
    app()
