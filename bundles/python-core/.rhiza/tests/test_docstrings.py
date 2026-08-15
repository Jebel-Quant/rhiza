"""Tests for module docstrings using doctest.

This file and its associated tests flow down via a SYNC action from the jebel-quant/rhiza repository
(https://github.com/jebel-quant/rhiza).

Automatically discovers all packages and runs doctests for each.

**Scope.** The folders searched come from ``RHIZA_DOCTEST_FOLDERS``, which ``quality.mk``
sets from python-core's ``DOCSTRING_FOLDERS`` accumulator — the same list ``make
docs-coverage`` uses. With the variable unset (running pytest by hand, say) it falls back
to ``SOURCE_FOLDER`` from ``.rhiza/.env``, defaulting to ``src``.

That indirection exists because this gate used to resolve ``src`` and nothing else, so a
project keeping Python outside its source root had its docstring examples silently
skipped — the mother repo being the extreme case, with no ``src/`` at all and 23 unchecked
examples in ``utils/`` (#1517). It is the same hole #1505 closed for the Makefile gates
and #1516 for coverage, in the shipped suite rather than in make.

**Two layouts, deliberately.** A folder may hold packages (``src/mypkg/__init__.py``) or
loose scripts (``utils/link_dogfood.py``); both carry docstrings worth checking, so both
are discovered. A module that cannot be imported is reported as a warning and skipped, not
failed: a loose script may execute at import, and "we could not measure this" is a
different statement from "this example is wrong".
"""

from __future__ import annotations

import doctest
import importlib
import importlib.util
import os
import warnings
from pathlib import Path

import pytest
from dotenv import dotenv_values

# Read .rhiza/.env at collection time (no environment side-effects).
RHIZA_ENV_PATH = Path(".rhiza/.env")

# Set by `make rhiza-test` from DOCSTRING_FOLDERS; whitespace-separated.
DOCTEST_FOLDERS_ENV = "RHIZA_DOCTEST_FOLDERS"


def _iter_modules_from_path(logger, package_path: Path, src_path: Path):
    """Recursively find all Python modules in a directory."""
    for path in package_path.rglob("*.py"):
        if path.name == "__init__.py":
            module_path = path.parent.relative_to(src_path)
        else:
            module_path = path.relative_to(src_path).with_suffix("")

        # Convert path to module name in an OS-independent way
        module_name = ".".join(module_path.parts)

        try:
            yield importlib.import_module(module_name)
        except ImportError as e:
            warnings.warn(f"Could not import {module_name}: {e}", stacklevel=2)
            logger.warning("Could not import module %s: %s", module_name, e)
            continue


def _find_packages(src_path: Path):
    """Find all packages in the source path, including those nested under namespace packages."""
    for init_file in src_path.rglob("__init__.py"):
        package_dir = init_file.parent
        # Only yield top-level packages (those whose parent doesn't have __init__.py or is src_path)
        parent = package_dir.parent
        if parent == src_path or not (parent / "__init__.py").exists():
            yield package_dir


def _doctest_folders(root: Path, values: dict) -> list[Path]:
    """Return the existing folders whose docstrings should be doctested.

    Args:
        root: The repository root.
        values: The parsed ``.rhiza/.env`` mapping.

    Returns:
        Each configured folder that exists, in order, without duplicates.
    """
    configured = os.environ.get(DOCTEST_FOLDERS_ENV, "").split()
    if not configured:
        configured = [values.get("SOURCE_FOLDER") or "src"]

    folders: list[Path] = []
    for name in configured:
        path = root / name
        if path.is_dir() and path not in folders:
            folders.append(path)
    return folders


def _iter_loose_modules(logger, folder: Path):
    """Import the top-level ``*.py`` files in ``folder`` that are not part of a package.

    A folder of standalone scripts (``utils/``, ``scripts/``, ``tools/``) has no
    ``__init__.py``, so :func:`_find_packages` never reaches it even though its docstrings
    may carry examples. Each file is loaded from its path rather than by module name, so
    no ``sys.path`` manipulation is needed and two folders may hold same-named scripts.

    Args:
        logger: The test logger.
        folder: The directory to scan (not recursed — a package below it is the other
            discovery path's job).

    Yields:
        Each imported module. A module that raises on import is warned about and skipped:
        a loose script may run code at import time, and being unable to measure an example
        is not the same as the example being wrong.
    """
    if (folder / "__init__.py").exists():
        return  # a package; _find_packages handles it

    for path in sorted(folder.glob("*.py")):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:  # pragma: no cover - defensive
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except BaseException as e:  # noqa: BLE001 - a script may raise or SystemExit on import
            warnings.warn(f"Could not import {path}: {e}", stacklevel=2)
            logger.warning("Could not import loose module %s: %s", path, e)
            continue
        yield module


def test_doctests(logger, root, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    """Run doctests for every module in the configured folders."""
    values = dotenv_values(root / RHIZA_ENV_PATH) if (root / RHIZA_ENV_PATH).exists() else {}
    folders = _doctest_folders(root, values)

    logger.info("Starting doctest discovery in: %s", [str(f) for f in folders] or "(nothing configured)")
    if not folders:
        configured = os.environ.get(DOCTEST_FOLDERS_ENV) or values.get("SOURCE_FOLDER") or "src"
        logger.info("No doctest folder exists (looked for: %s) — skipping doctests", configured)
        pytest.skip(f"No doctest folder found (looked for: {configured})")

    total_tests = 0
    total_failures = 0
    failed_modules = []

    def _run(module) -> None:
        """Run one module's doctests and fold the result into the running totals."""
        nonlocal total_tests, total_failures
        logger.debug("Running doctests for module: %s", module.__name__)
        # Disable pytest's stdout capture during doctest to avoid interference
        with capsys.disabled():
            results = doctest.testmod(
                module,
                verbose=False,
                optionflags=(doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE),
            )
        total_tests += results.attempted

        if results.failed:
            logger.warning(
                "Doctests failed for %s: %d/%d failed",
                module.__name__,
                results.failed,
                results.attempted,
            )
            total_failures += results.failed
            failed_modules.append((module.__name__, results.failed, results.attempted))
        else:
            logger.debug("Doctests passed for %s (%d test(s))", module.__name__, results.attempted)

    for src_path in folders:
        # Add the folder to sys.path with automatic cleanup
        monkeypatch.syspath_prepend(str(src_path))
        logger.debug("Prepended to sys.path: %s", src_path)

        # Find all packages in the folder (supports namespace packages)
        for package_dir in _find_packages(src_path):
            if package_dir.is_dir() and (package_dir / "__init__.py").exists():
                # Import the package
                package_name = package_dir.name
                logger.info("Discovered package: %s", package_name)
                try:
                    modules = list(_iter_modules_from_path(logger, package_dir, src_path))
                    logger.debug("%d module(s) found in package %s", len(modules), package_name)

                    for module in modules:
                        _run(module)

                except ImportError as e:
                    warnings.warn(f"Could not import package {package_name}: {e}", stacklevel=2)
                    logger.warning("Could not import package %s: %s", package_name, e)
                    continue

        # And the loose scripts, which no package walk reaches
        for module in _iter_loose_modules(logger, src_path):
            _run(module)

    if failed_modules:
        formatted = "\n".join(f"  {name}: {failed}/{attempted} failed" for name, failed, attempted in failed_modules)
        msg = (
            f"Doctest summary: {total_tests} tests across {len(failed_modules)} module(s)\n"
            f"Failures: {total_failures}\n"
            f"Failed modules:\n{formatted}"
        )
        logger.error("%s", msg)
        assert total_failures == 0, msg
    else:
        logger.info("Doctest summary: %d tests, 0 failures", total_tests)

    if total_tests == 0:
        logger.info("No doctests were found in any module — skipping")
        pytest.skip("No doctests were found in any module")
