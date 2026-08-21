r"""Every configured pre-commit hook must be able to see a file in this repository.

A hook whose ``files:`` pattern matches nothing is not an error to prek: it prints
``(no files to check)Skipped`` and the run stays green. That line reads like a check, in the
output of the gate this repo runs most, and the repo has now been bitten by it three times
through three different routes:

- **A pattern for a layout this repo does not have.** The bundle ships interrogate with
  ``files: ^src/``, right for a downstream project and inert here, so the hook skipped on
  every ``make fmt`` while ``make docs-coverage`` enforced a stricter bar (#1535).
- **A pattern for a path the template retired.** ``check-makefile-targets`` also matches
  ``^\\.rhiza/.*\\.mk$``, and the make fragments went in #1556.
- **A pattern for a path that became a symlink.** ``update-readme-help`` matches
  ``^Makefile$``; #1576 made the root Makefile a dogfood symlink into ``bundles/core/``, git
  tracks it as mode 120000, and prek classifies a symlink as ``symlink`` rather than
  ``file`` -- so a hook carrying pre-commit's default ``types: [file]`` is never handed it,
  even under ``--all-files``. The README's generated help block was stale for a release
  before anyone noticed (#1581).

The third route is why the candidate set below **excludes symlinks** unless a hook opts in.
Modelling prek's file typing any further than that would mean reimplementing ``identify``;
what matters is that the one rule this repo keeps tripping over is enforced, and
:func:`test_the_symlink_rule_is_what_makes_this_test_bite` is the positive control proving
it still is.

**A ``language: fail`` hook is exempt, and not as a special case.** Such a hook exists to
match nothing -- ``no-python-cache-files`` fails the commit precisely *when* its pattern
selects a file -- so an empty match set is its passing state rather than a silent skip. The
distinction this test draws is therefore not "does the pattern match" but "is a pattern that
matches nothing what this hook wanted".

**Scope: two halves, and neither needs the other.** The offline half checks every pattern
written in *this* config -- the overrides, which are where a mother-repo assumption gets
encoded. The network half checks the hooks from ``Jebel-Quant/rhiza-hooks``, whose patterns
name rhiza's own layout (``^Makefile$``, ``^\\.rhiza/template\\.yml$``) and therefore drift
when rhiza moves a file. Third-party hooks are deliberately out of scope: ruff and
markdownlint key on file extensions, which do not move.
"""

from __future__ import annotations

import functools
import re
import subprocess  # nosec B404 - fixed argument vectors
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG = _ROOT / ".pre-commit-config.yaml"

_RHIZA_HOOKS_REPO = "https://github.com/Jebel-Quant/rhiza-hooks"
_HOOKS_MANIFEST = "https://raw.githubusercontent.com/Jebel-Quant/rhiza-hooks/{rev}/.pre-commit-hooks.yaml"

# Hooks that legitimately match nothing *in this repository*, each with the reason. An entry
# here is a claim that the hook is inert by design rather than by accident -- so it is the
# review surface this test exists to create, and the list must stay short.
_INERT_BY_DESIGN = {
    # The mother repo has no `.rhiza/template.yml`: it *is* the template, so there is no
    # consumer config for the hook to validate. Enabled deliberately, so that a future
    # `template.yml` here (or a copy of this config in a consumer) starts being checked
    # without an edit.
    "check-rhiza-config": "the mother repo has no .rhiza/template.yml -- it is the template",
}

# Git's mode for a symlink. prek tags these `symlink`, not `file`, so a hook with
# pre-commit's default `types: [file]` never receives one.
_SYMLINK_MODE = "120000"


@functools.lru_cache(maxsize=1)
def _tracked() -> tuple[tuple[str, str], ...]:
    """Return every tracked path with its git mode, as ``(mode, path)`` pairs.

    Returns:
        One pair per tracked path, modes as the six-digit strings ``git ls-files -s`` prints.
    """
    proc = subprocess.run(  # nosec B603
        ["git", "ls-files", "-s"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    pairs = []
    for line in proc.stdout.splitlines():
        meta, _, path = line.partition("\t")
        pairs.append((meta.split()[0], path))
    return tuple(pairs)


def _candidates(hook: dict) -> list[str]:
    """Return the tracked paths prek could hand this hook.

    Symlinks are excluded unless the hook's ``types``/``types_or`` names ``symlink``: that is
    the rule the root Makefile broke, and the only part of prek's file typing modelled here.

    Args:
        hook: The effective hook config -- upstream definition with this repo's keys applied.

    Returns:
        The candidate paths, before the ``files``/``exclude`` patterns are applied.
    """
    declared = set(hook.get("types", []) or []) | set(hook.get("types_or", []) or [])
    wants_symlinks = "symlink" in declared
    return [path for mode, path in _tracked() if wants_symlinks or mode != _SYMLINK_MODE]


def _matches(hook: dict) -> list[str]:
    """Return the candidate paths this hook's patterns actually select.

    Args:
        hook: The effective hook config.

    Returns:
        Every candidate path matching ``files`` and not matching ``exclude``.
    """
    files = re.compile(hook["files"]) if hook.get("files") else None
    exclude = re.compile(hook["exclude"]) if hook.get("exclude") else None
    selected = []
    for path in _candidates(hook):
        if files is not None and not files.search(path):
            continue
        if exclude is not None and exclude.search(path):
            continue
        selected.append(path)
    return selected


@functools.lru_cache(maxsize=1)
def _config() -> dict:
    """Return the parsed root pre-commit config.

    Returns:
        The config mapping, with its ``repos`` list.
    """
    return yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))


def _configured_hooks(repo_url: str | None = None) -> list[dict]:
    """Return the hook entries this config declares, optionally for one repo.

    Args:
        repo_url: When given, only hooks from that ``repo:`` are returned.

    Returns:
        The hook mappings as written in this config, each carrying its own overrides only.
    """
    hooks = []
    for repo in _config()["repos"]:
        if repo_url is not None and repo.get("repo") != repo_url:
            continue
        hooks.extend(repo.get("hooks", []))
    return hooks


@functools.lru_cache(maxsize=1)
def _upstream_rhiza_hooks() -> dict[str, dict] | None:
    """Return rhiza-hooks' own hook definitions at the pinned rev.

    Fetched rather than listed here, because the whole failure mode is a pattern written
    upstream that this repo's layout has moved out from under -- a copy here would be one
    more thing to drift.

    Returns:
        ``{hook id: definition}``, or None when the network or the rev is unavailable.
    """
    rev = next(
        (r.get("rev") for r in _config()["repos"] if r.get("repo") == _RHIZA_HOOKS_REPO),
        None,
    )
    if not rev:
        return None
    try:
        # Suppressed below: the URL is this module's own https constant with a pinned rev
        # interpolated, the same shape as tests/bundles/test_gitlab_ci.py's fetches.
        with urllib.request.urlopen(_HOOKS_MANIFEST.format(rev=rev), timeout=20) as response:  # noqa: S310  # nosec B310
            manifest = yaml.safe_load(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, yaml.YAMLError):
        return None
    return {entry["id"]: entry for entry in manifest}


def _effective(hook: dict, upstream: dict) -> dict:
    """Merge this repo's hook entry over the upstream definition.

    Args:
        hook: The entry as written in this config.
        upstream: The hook's upstream definition.

    Returns:
        The upstream definition with every key this config restates replaced.
    """
    return {**upstream, **hook}


def _reachable(hook: dict) -> bool:
    """Report whether prek can hand this hook at least one file.

    ``always_run`` is the documented way to say a hook needs no file at all -- it is what
    ``update-readme-help`` uses here, and what upstream's
    ``check-python-version-consistency`` ships with.

    Args:
        hook: The effective hook config.

    Returns:
        True when the hook always runs, or when its patterns select a candidate.
    """
    return bool(hook.get("always_run")) or bool(_matches(hook))


def _is_tripwire(hook: dict) -> bool:
    """Report whether this hook exists in order to match nothing.

    pre-commit's ``language: fail`` means "if you are handed a file, fail" -- so a tripwire's
    passing state is an empty match set, and reachability is not a property it should have.
    ``no-python-cache-files`` is the one here. Keyed on the language rather than on the id, so
    the next tripwire added is classified correctly without an edit.

    Args:
        hook: The effective hook config.

    Returns:
        True when the hook is a guard against files existing at all.
    """
    return hook.get("language") == "fail"


_LOCALLY_SCOPED = [h for h in _configured_hooks() if h.get("files") and not _is_tripwire(h)]


@pytest.mark.parametrize("hook", _LOCALLY_SCOPED, ids=lambda h: str(h["id"]))
def test_a_pattern_written_here_selects_a_real_file(hook: dict) -> None:
    """Every ``files:`` pattern in this config must match a tracked file.

    The offline half. A pattern restated here is a mother-repo decision -- interrogate's
    ``^(utils|tests)/`` exists because the bundle's ``^src/`` matched nothing (#1535) -- so
    it is exactly the kind that goes stale when this repo's layout changes.
    """
    assert _matches(hook), (
        f"hook {hook['id']!r} declares files={hook['files']!r}, which matches no tracked "
        f"file. prek reports that as '(no files to check)Skipped' and the gate stays green, "
        f"so the hook is not checking anything (#1535, #1581)."
    )


def test_every_rhiza_hook_can_see_something() -> None:
    """rhiza-hooks' patterns name rhiza's own layout, so they drift when rhiza moves a file.

    The network half. Skips without the manifest, so ``make test`` stays green offline while
    CI does the real check -- the same bargain as ``test_bundle_cli_targets`` and
    ``test_gitlab_ci``.
    """
    upstream = _upstream_rhiza_hooks()
    if upstream is None:
        pytest.skip("could not fetch rhiza-hooks' .pre-commit-hooks.yaml")

    unreachable = []
    for entry in _configured_hooks(_RHIZA_HOOKS_REPO):
        hook_id = entry["id"]
        if hook_id in _INERT_BY_DESIGN or hook_id not in upstream:
            continue
        effective = _effective(entry, upstream[hook_id])
        if _is_tripwire(effective):
            continue
        if not _reachable(effective):
            unreachable.append(f"{hook_id} (files={upstream[hook_id].get('files')!r})")

    assert not unreachable, (
        f"these rhiza-hooks match no tracked file and are silently inert: {unreachable}. "
        f"Either set `always_run: true` (if the hook takes `pass_filenames: false`), narrow "
        f"the config to a path that exists, disable the hook with the reason recorded, or "
        f"add it to _INERT_BY_DESIGN with a reason. Do not set `always_run` on a hook that "
        f"takes filenames: it then loops over an empty list and reports Passed (#1581)."
    )


def test_the_symlink_rule_is_what_makes_this_test_bite() -> None:
    """Positive control: ``^Makefile$`` with default types must resolve to nothing.

    Without this, a change that stopped excluding symlinks would make every assertion above
    pass vacuously -- and the #1581 route would reopen with the guard still green. Asserted
    against the real root Makefile, which is a tracked symlink, so it also fails if the
    dogfood link is ever replaced by a real file (at which point the override in
    ``.pre-commit-config.yaml`` is no longer needed and its comment is wrong).
    """
    modes = {path: mode for mode, path in _tracked()}
    assert modes.get("Makefile") == _SYMLINK_MODE, (
        "the root Makefile is no longer a tracked symlink, so update-readme-help's "
        "`always_run: true` override and its comment in .pre-commit-config.yaml are stale"
    )
    assert not _matches({"id": "probe", "files": r"^Makefile$"}), (
        "a hook matching ^Makefile$ with pre-commit's default types now resolves to a file, "
        "so this suite would no longer catch #1581's symlink route"
    )
    assert _matches({"id": "probe", "files": r"^Makefile$", "types": ["symlink"]}), (
        "opting into symlinks no longer selects the root Makefile, so _candidates() is "
        "excluding more than it should and every assertion above is weaker than it reads"
    )
