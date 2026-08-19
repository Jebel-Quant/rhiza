"""Shared test utilities for rhiza test suite."""

from __future__ import annotations

import functools
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


@functools.lru_cache(maxsize=1)
def _shim_text() -> str:
    """Return the rhiza-task shim Makefile, generated once per session.

    Why the fixtures need this at all: ``core`` no longer ships a ``Makefile`` or a
    ``.rhiza/rhiza.mk``, so a project assembled from bundles by :func:`sync_bundles` has no
    front door and no loader for the five fragments that survive (docker, github, lfs, paper,
    presentation). Every test that drives ``make`` against such a project has to supply the
    shim, which is exactly what a real consumer does once with ``uvx rhiza-task shim > Makefile``.

    Generated from the *pinned* CLI rather than copied from the repo root, for two reasons: the
    root Makefile carries mother-repo-only targets that must not leak into a fixture, and
    generating it means these tests exercise the shim a consumer would actually get.

    Cached because it costs a subprocess and the answer cannot change within a session.

    Returns:
        The shim's text.

    Raises:
        pytest.skip.Exception: When the CLI cannot be reached, rather than failing every
            make-driven test with a confusing subprocess error.
    """
    root = Path(__file__).resolve().parents[1]
    match = re.search(r"^RHIZA_TASK \?= (\S+)", (root / "Makefile").read_text(encoding="utf-8"), re.MULTILINE)
    if not match:
        pytest.skip("the root Makefile no longer pins RHIZA_TASK, so no shim can be generated")
    proc = subprocess.run(  # nosec B603
        ["uvx", match.group(1), "shim"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        pytest.skip(f"could not generate the rhiza-task shim: {proc.stderr.strip()[:200]}")
    return proc.stdout


def write_shim(dest: Path) -> Path:
    """Write the rhiza-task shim into ``dest`` as its ``Makefile``.

    Also adds the fragment include the shipped shim does not carry yet
    (Jebel-Quant/rhiza-task#20), because without it the surviving ``.rhiza/make.d`` fragments
    are inert and every target they own reports "no rule to make target".

    Args:
        dest: The assembled project's root.

    Returns:
        The path written.
    """
    text = _shim_text()
    if "-include .rhiza/make.d/*.mk" not in text:
        text += (
            "\n# Added by the test harness: the shipped shim does not include the fragments yet\n"
            "# (Jebel-Quant/rhiza-task#20), and the surviving bundles' targets live in them.\n"
            "-include .rhiza/make.d/*.mk\n"
            ".rhiza/make.d/%.mk: ;\n"
        )
    makefile = dest / "Makefile"
    makefile.write_text(text, encoding="utf-8")
    return makefile


def run_make(
    logger: logging.Logger,
    args: list[str] | None = None,
    check: bool = True,
    dry_run: bool = True,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run make with optional arguments and return the completed process.

    ``cwd`` defaults to the process working directory, which is what the tests
    that chdir into a temp project rely on. The end-to-end suite passes it
    explicitly instead: its projects are built per module and outlive a single
    test, so chdir-ing would make the tests order- and worker-dependent.

    Decoding is pinned to UTF-8 rather than left to ``text=True``'s default, which is the
    *locale* codec — cp1252 on the Windows runners. The make fragments are UTF-8 and some
    print non-ASCII (`doctor`'s ✅/❌ markers), so on Windows the default decode raised
    ``UnicodeDecodeError`` inside subprocess, which surfaced as ``stdout`` being ``None``
    and then a ``TypeError`` several frames away in ``strip_ansi`` — a decoding problem
    wearing the mask of a type error. ``errors="replace"`` keeps any future stray byte
    from doing that again.
    """
    cmd = [_MAKE]
    if args:
        cmd.extend(args)
    cmd.insert(1, "-sn" if dry_run else "-s")
    logger.info("Running command: %s (cwd=%s)", " ".join(cmd), cwd or Path.cwd())
    result = subprocess.run(  # nosec B603
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, cwd=cwd
    )
    if check and result.returncode != 0:
        msg = f"make failed with code {result.returncode}:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        raise AssertionError(msg)
    return result


def setup_rhiza_git_repo() -> None:
    """Initialize a git repository in cwd and set remote to rhiza.

    Idempotent: safe to call again when an autouse fixture has already created the
    repo and its ``origin`` remote (as ``tests/api/conftest.py`` does), so migrated
    tests that call it in their bodies do not fail on a duplicate remote.
    """
    subprocess.run([_GIT, "init"], check=True, capture_output=True)  # nosec B603
    existing = subprocess.run([_GIT, "remote"], capture_output=True, text=True)  # nosec B603
    if "origin" not in existing.stdout.split():
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
