"""The `rhiza-test` package's own logic, tested from the mother repo.

The suite modules under ``rhiza_test.suite`` are pytest files executed against a
consuming repository — they are exercised by ``make rhiza-test``, not by ``make test``.
What is tested here is the code around them that is *not* itself a test: the shared fence
helper, and the collection-time layer detection.

That detection is the part worth pinning. While the suite was copied per-bundle the
selection was implicit — a Rust project simply never received ``test_pyproject.py``. One
shared distribution has to reconstruct it, and getting it wrong is silent in both
directions: collect too much and every Python repo fails on a missing ``Cargo.toml``;
collect too little and a Rust repo stops being checked by the very assertions that exist
for it.
"""

from __future__ import annotations

import importlib.util
import subprocess  # nosec B404
from pathlib import Path

import pytest

_PKG_SRC = Path(__file__).resolve().parents[2] / "packages" / "rhiza-test" / "src"


def _load(module_name: str, relative: str):
    """Import a module from the package source by path.

    Args:
        module_name: Name to register the loaded module under.
        relative: Path to the module, relative to the package ``src`` directory.

    Returns:
        The imported module object.
    """
    spec = importlib.util.spec_from_file_location(module_name, _PKG_SRC / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_fences = _load("rhiza_test_fences", "rhiza_test/_fences.py")
_suite_conftest = _load("rhiza_test_suite_conftest", "rhiza_test/suite/conftest.py")


class TestFenceFlags:
    """The shared `+RHIZA_SKIP` helper both README modules now import."""

    @pytest.mark.parametrize("flags", ["+RHIZA_SKIP", " +RHIZA_SKIP", " +RHIZA_SKIP other"])
    def test_flagged_fences_are_skipped(self, flags: str) -> None:
        """Any flag string containing the marker excludes the fence."""
        assert _fences.should_skip(flags) is True

    @pytest.mark.parametrize("flags", ["", " ", "other-flag"])
    def test_unflagged_fences_are_kept(self, flags: str) -> None:
        """A flag string without the marker leaves the fence in."""
        assert _fences.should_skip(flags) is False


class TestLayerDetection:
    """`pytest_ignore_collect` must collect exactly the layers a repo actually uses."""

    @staticmethod
    def _repo(tmp_path: Path, *files: str) -> Path:
        """Create a git repo containing the given (possibly nested) files."""
        for name in files:
            target = tmp_path / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # nosec B603 B607
        return tmp_path

    def _ignored(self, module: str, repo: Path, monkeypatch: pytest.MonkeyPatch) -> bool:
        """Report whether the hook would ignore *module* for the repo at *repo*."""
        monkeypatch.chdir(repo)
        return bool(_suite_conftest.pytest_ignore_collect(Path(module), None))

    def test_language_neutral_modules_are_always_collected(self, tmp_path, monkeypatch) -> None:
        """Core's modules apply to every repo, whatever it is written in."""
        repo = self._repo(tmp_path)
        for module in ("test_readme.py", "test_release_tags.py", "conftest.py"):
            assert self._ignored(module, repo, monkeypatch) is False

    def test_a_python_repo_does_not_collect_the_rust_or_go_modules(self, tmp_path, monkeypatch) -> None:
        """The failure this replaced: Cargo/Go assertions firing on a Python project."""
        repo = self._repo(tmp_path, ".rhiza/make.d/python.mk", "pyproject.toml")
        assert self._ignored("test_pyproject.py", repo, monkeypatch) is False
        assert self._ignored("test_cargo_toml.py", repo, monkeypatch) is True
        assert self._ignored("test_go_module.py", repo, monkeypatch) is True

    def test_a_rust_repo_collects_only_the_rust_module(self, tmp_path, monkeypatch) -> None:
        """A Rust layer must be checked by its own module and no other layer's."""
        repo = self._repo(tmp_path, ".rhiza/make.d/rust.mk", "Cargo.toml")
        assert self._ignored("test_cargo_toml.py", repo, monkeypatch) is False
        assert self._ignored("test_pyproject.py", repo, monkeypatch) is True
        assert self._ignored("test_go_module.py", repo, monkeypatch) is True

    def test_a_go_repo_collects_only_the_go_module(self, tmp_path, monkeypatch) -> None:
        """Likewise for the Go layer."""
        repo = self._repo(tmp_path, ".rhiza/make.d/go.mk", "go.mod")
        assert self._ignored("test_go_module.py", repo, monkeypatch) is False
        assert self._ignored("test_pyproject.py", repo, monkeypatch) is True
        assert self._ignored("test_cargo_toml.py", repo, monkeypatch) is True

    def test_the_make_fragment_alone_selects_a_layer(self, tmp_path, monkeypatch) -> None:
        """The manifest must not be the only signal, or the gate cannot fail on its loss.

        A Rust repo that has lost ``Cargo.toml`` is precisely what
        ``test_cargo_toml_exists`` is for. Keying collection on the manifest would make
        that test deselect itself in the one case it exists to catch, so the layer's make
        fragment — synced if and only if ``rust-core`` was adopted — decides first.
        """
        repo = self._repo(tmp_path, ".rhiza/make.d/rust.mk")
        assert self._ignored("test_cargo_toml.py", repo, monkeypatch) is False

    def test_a_repo_using_neither_signal_collects_no_layer_module(self, tmp_path, monkeypatch) -> None:
        """With no layer adopted and no manifest, no layer module applies."""
        repo = self._repo(tmp_path, "README.md")
        for module in ("test_pyproject.py", "test_cargo_toml.py", "test_go_module.py"):
            assert self._ignored(module, repo, monkeypatch) is True
