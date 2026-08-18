"""Pytest configuration and fixtures for the rhiza test suite.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Provides shared session-scoped fixtures (``root``, ``logger`` and ``latest_tag``) used
across the test modules.

Language-neutral by design: the fixtures resolve paths and read git, neither of which
depends on what the project is written in.

It also decides which of the layer-specific modules to collect. That cannot be left to
per-test skips, because the assertion each layer most needs is exactly the one a skip
would suppress: ``test_cargo_toml_exists`` must **fail** on a Rust project that has lost
its ``Cargo.toml``. While the suite was copied per-bundle the selection was implicit — a
Rust repo simply never received ``test_pyproject.py``. One shared distribution has to
reconstruct that, which is what :func:`pytest_ignore_collect` does.

Security Notes:
- S101 (assert usage): Asserts are appropriate in test code for validating conditions
"""

import logging
import pathlib
import shutil
import subprocess  # nosec B404

import pytest

_GIT = shutil.which("git") or "/usr/bin/git"

# Which layer each module belongs to; anything unlisted is language-neutral and always
# collected.
_MODULE_LAYER = {
    "test_pyproject.py": "python",
    "test_docstrings.py": "python",
    "test_readme_validation.py": "python",
    "test_cargo_toml.py": "rust",
    "test_go_module.py": "go",
}

# How to tell a layer is in use. The make fragment comes first and is the reliable half:
# `.rhiza/make.d/rust.mk` is synced if and only if `rust-core` was adopted, and it is not
# something any of these modules asserts about. The manifest is only a fallback for a repo
# that uses the suite without rhiza's make layer — and it is deliberately *second*, since
# keying on the manifest alone would be circular: a Rust repo that lost `Cargo.toml` would
# silently stop being checked by the very test that exists to catch that.
_LAYER_MARKERS = {
    "python": (".rhiza/make.d/python.mk", "pyproject.toml"),
    "rust": (".rhiza/make.d/rust.mk", "Cargo.toml"),
    "go": (".rhiza/make.d/go.mk", "go.mod"),
}


def _repo_root() -> pathlib.Path:
    """Return the repository under test, for use before fixtures are available."""
    result = subprocess.run(  # nosec B603
        [_GIT, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return pathlib.Path(result.stdout.strip())
    return pathlib.Path.cwd()


def pytest_ignore_collect(collection_path, config):
    """Skip collecting a layer's module when the repo under test is not of that language.

    Args:
        collection_path: Candidate file or directory pytest is about to collect.
        config: The active pytest config (unused; part of the hook signature).

    Returns:
        bool | None: True to ignore the path, None to leave the decision to pytest.
    """
    layer = _MODULE_LAYER.get(collection_path.name)
    if layer is None:
        return None
    root = _repo_root()
    return not any((root / marker).exists() for marker in _LAYER_MARKERS[layer])


@pytest.fixture(scope="session")
def root():
    """Return the root of the repository under test.

    Derived from the working directory, **not** from this file's location. The suite
    ships inside an installed distribution, so ``__file__`` points into a uv cache
    directory that has nothing to do with the project being checked; it only worked
    while these modules were copied into each repo as ``.rhiza/tests/``.

    ``git rev-parse --show-toplevel`` is the authority, so the gate behaves the same
    whether it is invoked from the repo root or a subdirectory. A tree that is not a
    git repository at all falls back to the working directory rather than failing —
    every assertion that genuinely needs git skips on its own.

    Returns:
        pathlib.Path: The repository root, or the working directory outside git.
    """
    result = subprocess.run(  # nosec B603
        [_GIT, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return pathlib.Path(result.stdout.strip())
    return pathlib.Path.cwd()


@pytest.fixture(scope="session")
def logger():
    """Provide a session-scoped logger for tests.

    Returns:
        logging.Logger: Logger configured for the test session.
    """
    return logging.getLogger(__name__)


@pytest.fixture(scope="session")
def latest_tag(root):
    """Return the newest ``vX.Y.Z`` git tag, skipping when the repo has none.

    Shared rather than per-module because each language layer asserts the same thing
    against a different file — ``[project].version``, ``[package].version``, or Go's
    ``Version`` constant — and because every layer's release config derives its current
    version from this tag.

    Args:
        root: Repository root, from the ``root`` fixture.

    Returns:
        str: The highest version tag, e.g. ``v1.3.1``.
    """
    result = subprocess.run(  # nosec B603
        [_GIT, "tag", "--list", "v*", "--sort=-version:refname"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    tags = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not tags:
        pytest.skip("No version tags found in repository")
    return tags[0]
