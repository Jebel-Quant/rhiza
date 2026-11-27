"""The zizmor hook audits the workflows rhiza runs and ships, with its exceptions file.

zizmor runs as a hook in the root ``.pre-commit-config.yaml``, which rhiza_ci.yml's
pre-commit job runs, so a finding fails the required ``CI gate``. It can stop measuring
without failing in three ways, and each test below closes one:

* the hook is removed, or its ``--config`` points at a file that no longer exists, in
  which case zizmor exits with an error, or (worse) at a different file;
* the hook's ``files`` pattern stops matching ``bundles/``, so the copies consumers
  receive are never audited — prek skips a hook with no matching files and reports it
  as skipped, not failed;
* an exception is added to the config without a reason next to it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from tests.util import ZIZMOR_HOOK_FILES

_ROOT = Path(__file__).resolve().parents[2]
_HOOK_REPO = "https://github.com/zizmorcore/zizmor-pre-commit"


def _zizmor_hook() -> dict:
    """Return the zizmor hook entry from the root pre-commit config."""
    config = yaml.safe_load((_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    for repo in config["repos"]:
        if repo["repo"] == _HOOK_REPO:
            hooks = [hook for hook in repo["hooks"] if hook["id"] == "zizmor"]
            assert len(hooks) == 1, f"expected one zizmor hook in {_HOOK_REPO}, got {hooks}"
            return hooks[0]
    pytest.fail(f"the root .pre-commit-config.yaml has no {_HOOK_REPO} hook")


def _config_path(hook: dict) -> Path:
    """Return the path the hook passes to --config."""
    args = hook.get("args", [])
    assert "--config" in args, f"the zizmor hook passes no --config: {args}"
    return _ROOT / args[args.index("--config") + 1]


class TestZizmorGate:
    """The hook is wired, reads the exceptions file, and audits the bundles."""

    def test_hook_reads_an_existing_config(self) -> None:
        """--config names the committed exceptions file."""
        path = _config_path(_zizmor_hook())
        assert path == _ROOT / ".github" / "zizmor.yml", f"unexpected zizmor config {path}"
        assert path.is_file(), f"{path.relative_to(_ROOT)} does not exist"

    def test_hook_runs_offline(self) -> None:
        """Without --offline, a GH_TOKEN in the environment changes which audits run."""
        assert "--offline" in _zizmor_hook().get("args", [])

    def test_hook_does_not_narrow_the_upstream_file_set(self) -> None:
        """A local `files`/`exclude` override could drop bundles/ without failing anything."""
        hook = _zizmor_hook()
        assert "files" not in hook, "keep the upstream `files` pattern; it is what reaches bundles/"
        assert "exclude" not in hook, "an exclude would silently stop auditing what it matches"

    def test_bundle_workflows_are_in_scope(self) -> None:
        """Both the live workflows and the shipped bundle copies match the hook's pattern."""
        pattern = re.compile(ZIZMOR_HOOK_FILES)
        live = [p for p in (_ROOT / ".github" / "workflows").glob("*.yml") if pattern.search(p.as_posix())]
        shipped = [p for p in _ROOT.glob("bundles/*/.github/workflows/*.yml") if pattern.search(p.as_posix())]
        assert len(live) >= 10, f"expected the live workflows in scope, got {len(live)}"
        assert len(shipped) >= 10, f"expected the bundle workflows in scope, got {len(shipped)}"

    def test_every_exception_has_a_reason(self) -> None:
        """Each rule entry in .github/zizmor.yml is preceded by an explanatory comment."""
        text = (_ROOT / ".github" / "zizmor.yml").read_text(encoding="utf-8")
        rules = yaml.safe_load(text)["rules"]
        lines = text.splitlines()
        for rule in rules:
            start = next(i for i, line in enumerate(lines) if line.strip() == f"{rule}:")
            body = lines[start + 1 : start + 1 + _rule_length(lines, start)]
            assert any(line.strip().startswith("#") for line in body), f"{rule}: add a comment saying why"


def _rule_length(lines: list[str], start: int) -> int:
    """Return how many lines after ``start`` belong to the rule block that begins there."""
    indent = len(lines[start]) - len(lines[start].lstrip())
    count = 0
    for line in lines[start + 1 :]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        count += 1
    return count
