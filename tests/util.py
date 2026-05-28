"""Shared test utilities for rhiza test suite."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest

_MAKE = shutil.which("make") or "/usr/bin/make"
_GIT = shutil.which("git") or "/usr/bin/git"
_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    return _ANSI_RE.sub("", text)


def run_make(
    logger: logging.Logger,
    args: list[str] | None = None,
    check: bool = True,
    dry_run: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run make with optional arguments and return the completed process."""
    cmd = [_MAKE]
    if args:
        cmd.extend(args)
    cmd.insert(1, "-sn" if dry_run else "-s")
    logger.info("Running command: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)  # nosec B603
    if check and result.returncode != 0:
        msg = f"make failed with code {result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        raise AssertionError(msg)
    return result


def setup_rhiza_git_repo() -> None:
    """Initialize a git repository in cwd and set remote to rhiza."""
    subprocess.run([_GIT, "init"], check=True, capture_output=True)  # nosec B603
    subprocess.run(  # nosec B603
        [_GIT, "remote", "add", "origin", "https://github.com/jebel-quant/rhiza"],
        check=True,
        capture_output=True,
    )


def _copy_entry(src: Path, dest: Path) -> None:
    """Copy src into dest, resolving any symlink to get the real content."""
    real = src.resolve() if src.is_symlink() else src
    dest.parent.mkdir(parents=True, exist_ok=True)
    if real.is_dir():
        shutil.copytree(real, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(real, dest)


def sync_bundles(root: Path, bundle_names: list[str], dest: Path) -> None:
    """Copy all files from the named bundles into dest.

    Walks each bundle directory without following symlinks, so directory
    symlinks are copied as whole resolved trees and file symlinks have their
    real content copied.
    """
    for name in bundle_names:
        bundle_dir = root / "bundles" / name
        if not bundle_dir.is_dir():
            pytest.fail(f"Bundle directory does not exist: bundles/{name}")

        for dirpath, dirs, files in os.walk(bundle_dir, followlinks=False):
            current = Path(dirpath)

            for d in dirs[:]:
                child = current / d
                if child.is_symlink():
                    dirs.remove(d)
                    _copy_entry(child, dest / child.relative_to(bundle_dir))

            for f in files:
                child = current / f
                _copy_entry(child, dest / child.relative_to(bundle_dir))
