"""Shared fixtures for CI/API tests.

Security Notes:
- S603 (subprocess without shell=True): subprocess calls use command lists, not user input
- S607 (subprocess with partial path): executables resolved from PATH in controlled test env
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from tests.util import setup_rhiza_git_repo, sync_bundles

# The bundles these tests assemble into a temp project. Sourced from ``bundles/`` rather
# than from the repo root, which is the change this repo's own migration forced: rhiza runs
# on the ``rhiza-task`` shim, so there is no root ``.rhiza/rhiza.mk`` to copy. Assembling
# from where the files live also means these tests assert what a *consumer* receives rather
# than what the mother repo happens to run.
SANDBOX_BUNDLES = [
    "core",
    "python-core",
    "book",
    "presentation",
    "github",
    "docker",
]


@pytest.fixture(autouse=True)
def setup_tmp_makefile(logger, root: Path, tmp_path: Path):
    """Copy Makefile and split files into a temp dir and chdir there."""
    # `core` ships the Makefile, so the assembled project has its front door with no extra
    # step -- which is the point of the template owning it rather than the CLI printing it.
    sync_bundles(root, SANDBOX_BUNDLES, tmp_path)
    (tmp_path / ".rhiza").mkdir(exist_ok=True)

    if (root / ".python-version").exists():
        shutil.copy(root / ".python-version", tmp_path / ".python-version")

    env_src = root / ".rhiza" / ".env"
    if env_src.exists():
        shutil.copy(env_src, tmp_path / ".rhiza" / ".env")
    else:
        (tmp_path / ".rhiza" / ".env").write_text("CUSTOM_SCRIPTS_FOLDER=.rhiza/customisations/scripts\n")

    (tmp_path / ".rhiza" / "template.yml").write_text("repository: Jebel-Quant/rhiza\nref: v0.7.1\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    setup_rhiza_git_repo()
    try:
        yield
    finally:
        os.chdir(old_cwd)
