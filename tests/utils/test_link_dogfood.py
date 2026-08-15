"""Unit tests for link_dogfood.py."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _load_module(root: Path):
    """Load ``utils/link_dogfood.py`` as an importable module."""
    module_path = root / "utils" / "link_dogfood.py"
    spec = importlib.util.spec_from_file_location("link_dogfood", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_link_one_keeps_original_file_when_temp_symlink_creation_fails(root, tmp_path, monkeypatch) -> None:
    """A failed temporary symlink creation should not delete the original file."""
    module = _load_module(root)
    rel = "file.txt"
    source = tmp_path / "source.txt"
    source.write_text("source", encoding="utf-8")
    link = tmp_path / rel
    link.write_text("original", encoding="utf-8")

    def _raise_symlink(self: Path, target: str, target_is_directory: bool = False) -> None:
        """Stand-in for ``Path.symlink_to`` that always fails."""
        raise OSError("boom")

    monkeypatch.setattr(Path, "symlink_to", _raise_symlink)

    with pytest.raises(OSError, match="boom"):
        module._link_one(tmp_path, rel, source)

    assert link.exists()
    assert not link.is_symlink()
    assert link.read_text(encoding="utf-8") == "original"


def test_classify_dogfood_skips_without_reading_mismatched_sizes(root, tmp_path, monkeypatch) -> None:
    """Owners with non-matching sizes should be skipped before byte reads."""
    module = _load_module(root)
    rel = "file.txt"
    root_file = tmp_path / rel
    root_file.write_text("abc", encoding="utf-8")
    owner = tmp_path / "owner.txt"
    owner.write_text("different-size", encoding="utf-8")
    index = {rel: [owner]}

    def _fail_read_bytes(self: Path) -> bytes:
        """Stand-in for ``Path.read_bytes`` that must never be invoked here."""
        msg = "read_bytes should not be called for mismatched file sizes"
        raise AssertionError(msg)

    monkeypatch.setattr(Path, "read_bytes", _fail_read_bytes)

    assert module._classify_dogfood(tmp_path, rel, index) == ("skip", None)


def test_relink_check_mode_reports_pending_and_exits_nonzero(root, tmp_path) -> None:
    """Check mode should accumulate pending links and exit non-zero when any are pending."""
    module = _load_module(root)

    rel_pending = "pending.txt"
    rel_unchanged = "unchanged.txt"

    # dst_pending is a real file (not a symlink) with the same content as src_pending —
    # it looks like an unlinked dogfood copy and should be flagged as pending.
    src_pending = tmp_path / "src_pending.txt"
    src_pending.write_text("pending-source", encoding="utf-8")
    dst_pending = tmp_path / rel_pending
    dst_pending.write_text("pending-source", encoding="utf-8")

    # dst_unchanged is already a correct *relative* symlink pointing at src_unchanged —
    # _link_is_current requires a relative target, so symlink_to must receive a str.
    src_unchanged = tmp_path / "src_unchanged.txt"
    src_unchanged.write_text("unchanged-source", encoding="utf-8")
    dst_unchanged = tmp_path / rel_unchanged
    dst_unchanged.symlink_to("src_unchanged.txt")  # relative symlink

    index = {
        rel_pending: [src_pending],
        rel_unchanged: [src_unchanged],
    }

    rc = module.relink(tmp_path, index, check=True)
    assert rc != 0


def test_classify_dogfood_relinks_a_dangling_symlink(root, tmp_path) -> None:
    """Moving a bundle file between bundles leaves the root symlink pointing at nothing.

    Before, `_classify_dogfood` stat'd the link and died with FileNotFoundError, so
    `make sync-self` — the very command that repairs the link — could not run. With no
    bytes to compare, the sole owner is the answer.
    """
    module = _load_module(root)
    rel = "file.txt"
    (tmp_path / rel).symlink_to(tmp_path / "gone" / "file.txt")
    owner = tmp_path / "owner.txt"
    owner.write_text("content", encoding="utf-8")

    assert module._classify_dogfood(tmp_path, rel, {rel: [owner]}) == ("link", owner)


def test_classify_dogfood_refuses_to_guess_a_dangling_symlink_with_two_owners(root, tmp_path) -> None:
    """Two candidate bundles and no bytes to compare — the linker must not pick one."""
    module = _load_module(root)
    rel = "file.txt"
    (tmp_path / rel).symlink_to(tmp_path / "gone" / "file.txt")
    owners = []
    for name in ("a.txt", "b.txt"):
        owner = tmp_path / name
        owner.write_text("content", encoding="utf-8")
        owners.append(owner)

    assert module._classify_dogfood(tmp_path, rel, {rel: owners}) == ("ambiguous", None)


# The tests below were added with #1516, which brought utils/ under the coverage gate for
# the first time: `make test` had measured only SOURCE_FOLDER, which does not exist here,
# so this module's happy paths — every branch that actually writes a symlink — had never
# been executed by anything. They are grouped by the function under test rather than
# interleaved above, so the pre-existing regression tests stay legible as a set.


def test_link_one_creates_a_relative_symlink(root, tmp_path) -> None:
    """The write path must produce a *relative* link and report that it created one."""
    module = _load_module(root)
    rel = "file.txt"
    source = tmp_path / "bundles" / "core" / "file.txt"
    source.parent.mkdir(parents=True)
    source.write_text("content", encoding="utf-8")
    (tmp_path / rel).write_text("content", encoding="utf-8")

    assert module._link_one(tmp_path, rel, source) is True

    link = tmp_path / rel
    assert link.is_symlink()
    # Relative, not absolute: an absolute target would break for every other checkout.
    assert os.readlink(link) == os.path.join("bundles", "core", "file.txt")
    assert link.read_text(encoding="utf-8") == "content"


def test_link_one_is_idempotent(root, tmp_path) -> None:
    """A second run over an already-correct link must be a no-op, not a rewrite.

    This is what makes `make sync-self` safe to run repeatedly and what lets
    `sync-self-check` distinguish "already linked" from "would link".
    """
    module = _load_module(root)
    rel = "file.txt"
    source = tmp_path / "bundles" / "core" / "file.txt"
    source.parent.mkdir(parents=True)
    source.write_text("content", encoding="utf-8")
    (tmp_path / rel).write_text("content", encoding="utf-8")

    assert module._link_one(tmp_path, rel, source) is True
    assert module._link_one(tmp_path, rel, source) is False


def test_link_one_removes_the_temp_link_when_replace_fails(root, tmp_path, monkeypatch) -> None:
    """A failure *after* the temporary symlink exists must not leave it behind.

    The `finally` branch is the only thing standing between a crashed run and a
    repository littered with `.file.txt.XXXX` symlinks that git would then report.
    """
    module = _load_module(root)
    rel = "file.txt"
    source = tmp_path / "source.txt"
    source.write_text("content", encoding="utf-8")
    (tmp_path / rel).write_text("original", encoding="utf-8")

    def _raise_replace(self: Path, target) -> None:
        """Stand-in for ``Path.replace`` that always fails."""
        msg = "replace failed"
        raise OSError(msg)

    monkeypatch.setattr(Path, "replace", _raise_replace)

    with pytest.raises(OSError, match="replace failed"):
        module._link_one(tmp_path, rel, source)

    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".file.txt.")]
    assert leftovers == [], f"temporary symlinks left behind: {leftovers}"
    assert (tmp_path / rel).read_text(encoding="utf-8") == "original"


def test_owner_by_content_skips_when_sizes_match_but_bytes_differ(root, tmp_path) -> None:
    """Equal size is only the cheap pre-filter — differing bytes still mean 'leave it real'."""
    module = _load_module(root)
    root_file = tmp_path / "file.txt"
    root_file.write_text("aaa", encoding="utf-8")
    owner = tmp_path / "owner.txt"
    owner.write_text("bbb", encoding="utf-8")  # same length, different content

    assert module._owner_by_content(root_file, [owner]) == ("skip", None)


def test_owner_by_content_is_ambiguous_when_two_owners_match(root, tmp_path) -> None:
    """Byte-identical to two bundles: refuse to guess an owner rather than pick one."""
    module = _load_module(root)
    root_file = tmp_path / "file.txt"
    root_file.write_text("content", encoding="utf-8")
    owners = []
    for name in ("a.txt", "b.txt"):
        owner = tmp_path / name
        owner.write_text("content", encoding="utf-8")
        owners.append(owner)

    assert module._owner_by_content(root_file, owners) == ("ambiguous", None)


@pytest.mark.parametrize(
    "rel",
    [
        "bundles/core/ruff.toml",  # a bundle source itself
        ".python-version",  # a declared mother-repo override
        ".github/dependabot.yml",  # GitHub does not resolve symlinks
        ".rhiza/.gitignore",  # git opens this with O_NOFOLLOW
    ],
)
def test_classify_dogfood_skips_bundle_sources_and_carveouts(root, tmp_path, rel: str) -> None:
    """Every carve-out reason must short-circuit before any content comparison."""
    module = _load_module(root)
    target = tmp_path / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("content", encoding="utf-8")
    owner = tmp_path / "owner.txt"
    owner.write_text("content", encoding="utf-8")

    assert module._classify_dogfood(tmp_path, rel, {rel: [owner]}) == ("skip", None)


def test_classify_dogfood_skips_a_path_with_no_bundle_owner(root, tmp_path) -> None:
    """A root-only file (no bundle claims its path) is not a dogfood copy."""
    module = _load_module(root)
    (tmp_path / "root_only.txt").write_text("content", encoding="utf-8")

    assert module._classify_dogfood(tmp_path, "root_only.txt", {}) == ("skip", None)


def test_report_names_each_ambiguous_path_and_fails(root, capsys) -> None:
    """An ambiguous match must be named on stdout, not just counted, and must exit non-zero."""
    module = _load_module(root)

    rc = module._report(check=False, linked=0, unchanged=1, ambiguous=["shared.toml"], pending=[])

    assert rc == 1
    out = capsys.readouterr().out
    assert "shared.toml" in out
    assert "ambiguous" in out


def test_report_succeeds_when_nothing_is_ambiguous_or_pending(root, capsys) -> None:
    """The all-clear path returns 0 and still prints a summary line."""
    module = _load_module(root)

    rc = module._report(check=False, linked=2, unchanged=3, ambiguous=[], pending=[])

    assert rc == 0
    assert "2 linked, 3 already correct" in capsys.readouterr().out


def test_relink_exits_when_there_is_no_bundles_directory(root, tmp_path) -> None:
    """Run from the wrong directory, the linker must say so rather than link nothing quietly."""
    module = _load_module(root)

    with pytest.raises(SystemExit) as excinfo:
        module.relink(tmp_path)

    assert "No bundles/ directory found" in str(excinfo.value)


def test_relink_write_mode_links_skips_and_flags_ambiguity(root, tmp_path, capsys) -> None:
    """One pass must link the eligible copy, skip the carve-out, and flag the ambiguous one."""
    module = _load_module(root)

    linkable = tmp_path / "linkable.txt"
    linkable.write_text("linkable", encoding="utf-8")
    source = tmp_path / "source.txt"
    source.write_text("linkable", encoding="utf-8")

    # A declared mother-repo override: it has an owner but must stay a real file.
    carveout = tmp_path / ".python-version"
    carveout.write_text("3.12", encoding="utf-8")
    carveout_owner = tmp_path / "owner-version.txt"
    carveout_owner.write_text("3.12", encoding="utf-8")

    shared = tmp_path / "shared.toml"
    shared.write_text("shared", encoding="utf-8")
    shared_owners = []
    for name in ("owner_a.toml", "owner_b.toml"):
        owner = tmp_path / name
        owner.write_text("shared", encoding="utf-8")
        shared_owners.append(owner)

    index = {
        "linkable.txt": [source],
        ".python-version": [carveout_owner],
        "shared.toml": shared_owners,
    }

    rc = module.relink(tmp_path, index)

    assert rc == 1, "an ambiguous match must fail the run"
    assert linkable.is_symlink(), "the eligible copy should have been linked"
    assert not carveout.is_symlink(), "a declared override must stay a real file"
    assert not shared.is_symlink(), "an ambiguous match must not be guessed"

    out = capsys.readouterr().out
    assert "1 linked, 0 already correct, 1 ambiguous" in out


def test_relink_counts_an_already_correct_link_as_unchanged(root, tmp_path, capsys) -> None:
    """Re-running over a linked tree must report it unchanged and succeed."""
    module = _load_module(root)
    source = tmp_path / "source.txt"
    source.write_text("content", encoding="utf-8")
    (tmp_path / "linked.txt").symlink_to("source.txt")

    rc = module.relink(tmp_path, {"linked.txt": [source]})

    assert rc == 0
    assert "0 linked, 1 already correct, 0 ambiguous" in capsys.readouterr().out


def test_relink_scans_bundles_and_git_when_given_no_index(root, tmp_path) -> None:
    """With no index, the real entry point reads bundles/ and `git ls-files`.

    This is the only test that exercises `_bundle_index` and `_tracked_files` together,
    i.e. the path `make sync-self` actually takes.
    """
    module = _load_module(root)
    git = shutil.which("git")
    if git is None:  # pragma: no cover - git is present on every supported runner
        pytest.skip("git is not installed")

    source = tmp_path / "bundles" / "core" / "ruff.toml"
    source.parent.mkdir(parents=True)
    source.write_text("line-length = 120\n", encoding="utf-8")
    (tmp_path / "ruff.toml").write_text("line-length = 120\n", encoding="utf-8")

    for args in (
        ["init", "-q"],
        ["-c", "user.email=t@example.com", "-c", "user.name=T", "add", "-A"],
        ["-c", "user.email=t@example.com", "-c", "user.name=T", "commit", "-qm", "initial"],
    ):
        subprocess.run([git, *args], cwd=tmp_path, check=True, capture_output=True)

    assert module.relink(tmp_path) == 0
    assert (tmp_path / "ruff.toml").is_symlink()
    # The bundle source itself must never be linked to itself.
    assert not source.is_symlink()


def test_parse_args_defaults_to_write_mode(root) -> None:
    """With no flags the tool writes — the historical default, preserved (#1531)."""
    module = _load_module(root)

    assert module._parse_args([]).check is False


def test_parse_args_accepts_the_check_flag(root) -> None:
    """``--check`` selects the non-writing drift check."""
    module = _load_module(root)

    assert module._parse_args(["--check"]).check is True


def test_parse_args_rejects_an_unknown_flag(root, capsys) -> None:
    """A mistyped flag must fail, not silently fall through to the writing run.

    This is the whole point of #1531: the previous ``"--check" in sys.argv[1:]`` scan
    treated ``--checks`` as "no flag given", so a user who asked for a preview got the
    run that rewrites tracked files as symlinks instead.
    """
    module = _load_module(root)

    with pytest.raises(SystemExit) as excinfo:
        module._parse_args(["--checks"])

    assert excinfo.value.code == 2
    assert "unrecognized arguments: --checks" in capsys.readouterr().err


def test_parse_args_documents_check_in_its_help(root, capsys) -> None:
    """``--help`` must describe ``--check`` rather than leaving it to be read in the source."""
    module = _load_module(root)

    with pytest.raises(SystemExit) as excinfo:
        module._parse_args(["--help"])

    assert excinfo.value.code == 0
    assert "--check" in capsys.readouterr().out
