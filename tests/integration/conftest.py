"""Fixtures for rhiza-specific integration tests.

These tests live in tests/ (not .rhiza/tests/) and do not sync downstream.

Two git-repo fixtures are provided:

* ``git_repo`` — a *rich* sandbox: a bare remote + local clone with the core Rhiza
  Makefiles (``rhiza.mk`` + ``.rhiza/make.d/``), the ``book/`` tree, and mock
  ``uv``/``make`` executables on ``PATH``. Makefile-target integration tests
  (book, docs, test.mk, virtual-env, lfs, docker, marimo, paper, presentation,
  benchmark) drive real ``make`` against it.
* ``minimal_git_repo`` — a bare git repo with only a ``pyproject.toml`` and the
  developer's real ``PATH``. Used by tests that must invoke the *real* ``uv``
  (e.g. SBOM generation), where the mock ``uv`` would get in the way.

Security Notes:
- S603 (subprocess without shell=True): subprocess calls use command lists, not user input
- S607 (subprocess with partial path): executables resolved from PATH in controlled test env
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest

GIT = shutil.which("git") or "/usr/bin/git"

MOCK_MAKE_SCRIPT = """#!/usr/bin/env python3
import sys

if len(sys.argv) > 1 and sys.argv[1] == "help":
    print("Mock Makefile Help")
    print("target: ## Description")
"""

MOCK_UV_SCRIPT = """#!/usr/bin/env python3
import sys
import re

try:
    from packaging.version import parse, InvalidVersion
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False

def get_version():
    with open("pyproject.toml", "r") as f:
        content = f.read()
    match = re.search(r'version = "(.*?)"', content)
    return match.group(1) if match else "0.0.0"

def set_version(new_version):
    with open("pyproject.toml", "r") as f:
        content = f.read()
    new_content = re.sub(r'version = ".*?"', f'version = "{new_version}"', content)
    with open("pyproject.toml", "w") as f:
        f.write(new_content)

def bump_version(current, bump_type):
    major, minor, patch = map(int, current.split('.'))
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return current

def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(1)

    if args[0] != "version":
        sys.exit(1)

    if "--short" in args and "--bump" not in args:
        print(get_version())
        return

    if "--bump" in args and "--dry-run" in args and "--short" in args:
        bump_idx = args.index("--bump") + 1
        bump_type = args[bump_idx]
        current = get_version()
        print(bump_version(current, bump_type))
        return

    if "--bump" in args and "--dry-run" not in args:
        bump_idx = args.index("--bump") + 1
        bump_type = args[bump_idx]
        current = get_version()
        new_ver = bump_version(current, bump_type)
        set_version(new_ver)
        return

    if len(args) >= 2 and not args[1].startswith("-") and "--dry-run" in args:
        version = args[1]
        if HAS_PACKAGING:
            try:
                parse(version)
            except InvalidVersion:
                sys.exit(1)
        else:
            if not re.match(r"^\\d", version):
                sys.exit(1)
        return

    if len(args) == 2 and not args[1].startswith("-"):
        set_version(args[1])
        return

if __name__ == "__main__":
    main()
"""


@pytest.fixture
def git_repo(root, tmp_path, monkeypatch) -> Path:
    """Sets up a remote bare repo and a local clone with the core Rhiza Makefiles.

    Mock ``uv``/``make`` executables are placed first on ``PATH`` so target logic
    can be exercised without touching the real toolchain.
    """
    remote_dir = tmp_path / "remote.git"
    local_dir = tmp_path / "local"

    # 1. Create bare remote
    remote_dir.mkdir()
    subprocess.run([GIT, "init", "--bare", str(remote_dir)], check=True)  # nosec B603
    subprocess.run([GIT, "symbolic-ref", "HEAD", "refs/heads/master"], cwd=remote_dir, check=True)  # nosec B603

    # 2. Clone to local
    subprocess.run([GIT, "clone", str(remote_dir), str(local_dir)], check=True)  # nosec B603

    monkeypatch.chdir(local_dir)

    subprocess.run([GIT, "checkout", "-b", "master"], check=True)  # nosec B603

    with open("pyproject.toml", "w") as f:
        f.write('[project]\nname = "test-project"\nversion = "0.1.0"\n')

    with open("uv.lock", "w") as f:
        f.write("")

    bin_dir = local_dir / "bin"
    bin_dir.mkdir()

    uv_path = bin_dir / "uv"
    with open(uv_path, "w") as f:
        f.write(MOCK_UV_SCRIPT)
    uv_path.chmod(0o755)

    make_path = bin_dir / "make"
    with open(make_path, "w") as f:
        f.write(MOCK_MAKE_SCRIPT)
    make_path.chmod(0o755)

    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ.get('PATH', '')}")

    # Copy core Rhiza Makefiles
    (local_dir / ".rhiza").mkdir(parents=True, exist_ok=True)
    shutil.copy(root / ".rhiza" / "rhiza.mk", local_dir / ".rhiza" / "rhiza.mk")
    shutil.copy(root / "Makefile", local_dir / "Makefile")

    make_d_src = root / ".rhiza" / "make.d"
    if make_d_src.is_dir():
        make_d_dst = local_dir / ".rhiza" / "make.d"
        shutil.copytree(make_d_src, make_d_dst, dirs_exist_ok=True)

    book_src = root / "book"
    book_dst = local_dir / "book"
    if book_src.is_dir():
        shutil.copytree(book_src, book_dst, dirs_exist_ok=True)

    subprocess.run([GIT, "config", "user.email", "test@example.com"], check=True)  # nosec B603
    subprocess.run([GIT, "config", "user.name", "Test User"], check=True)  # nosec B603
    subprocess.run([GIT, "add", "."], check=True)  # nosec B603
    subprocess.run([GIT, "commit", "-m", "Initial commit"], check=True)  # nosec B603
    subprocess.run([GIT, "push", "origin", "master"], check=True)  # nosec B603

    return local_dir


@pytest.fixture
def minimal_git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Provide a temporary directory with a minimal git repo and pyproject.toml.

    Unlike ``git_repo`` this does not shadow the real ``uv`` on ``PATH``, so tests
    that must run the actual toolchain (e.g. SBOM generation) use this fixture.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test-project"\nversion = "0.1.0"\n')
    subprocess.run([GIT, "init"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([GIT, "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    subprocess.run([GIT, "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)  # nosec B603
    return tmp_path
