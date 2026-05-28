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

from tests.util import setup_rhiza_git_repo

SPLIT_MAKEFILES = [
    ".rhiza/rhiza.mk",
    ".rhiza/make.d/bootstrap.mk",
    ".rhiza/make.d/quality.mk",
    ".rhiza/make.d/releasing.mk",
    ".rhiza/make.d/doctor.mk",
    ".rhiza/make.d/test.mk",
    ".rhiza/make.d/book.mk",
    ".rhiza/make.d/marimo.mk",
    ".rhiza/make.d/presentation.mk",
    ".rhiza/make.d/github.mk",
    ".rhiza/make.d/agentic.mk",
    ".rhiza/make.d/gh-aw.mk",
    ".rhiza/make.d/docker.mk",
]


@pytest.fixture(autouse=True)
def setup_tmp_makefile(logger, root: Path, tmp_path: Path):
    """Copy Makefile and split files into a temp dir and chdir there."""
    shutil.copy(root / "Makefile", tmp_path / "Makefile")
    (tmp_path / ".rhiza").mkdir(exist_ok=True)
    shutil.copy(root / ".rhiza" / "rhiza.mk", tmp_path / ".rhiza" / "rhiza.mk")

    if (root / ".python-version").exists():
        shutil.copy(root / ".python-version", tmp_path / ".python-version")

    env_src = root / ".rhiza" / ".env"
    if env_src.exists():
        shutil.copy(env_src, tmp_path / ".rhiza" / ".env")
    else:
        (tmp_path / ".rhiza" / ".env").write_text("CUSTOM_SCRIPTS_FOLDER=.rhiza/customisations/scripts\n")

    for split_file in SPLIT_MAKEFILES:
        src = root / split_file
        if src.exists():
            dst = tmp_path / split_file
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)

    if (root / ".rhiza" / ".rhiza-version").exists():
        shutil.copy(root / ".rhiza" / ".rhiza-version", tmp_path / ".rhiza" / ".rhiza-version")

    (tmp_path / ".rhiza" / "template.yml").write_text("repository: Jebel-Quant/rhiza\nref: v0.7.1\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    old_cwd = Path.cwd()
    os.chdir(tmp_path)
    setup_rhiza_git_repo()
    try:
        yield
    finally:
        os.chdir(old_cwd)
