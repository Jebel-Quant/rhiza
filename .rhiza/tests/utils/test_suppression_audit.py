"""Unit tests for suppression_audit.py helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_utils import strip_ansi


def _load_module(root: Path):
    """Import the repo's suppression_audit.py utility as a standalone module."""
    module_path = root / ".rhiza" / "utils" / "suppression_audit.py"
    spec = importlib.util.spec_from_file_location("suppression_audit", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["suppression_audit"] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# CVE extraction and pip-audit parsing
# ---------------------------------------------------------------------------


def test_nosec_cves_extracts_only_nosec_entries(root):
    """Only # nosec suppressions with CVE tags should be captured."""
    module = _load_module(root)

    suppressions = [
        module.Suppression(file="a.py", line_no=1, kind="nosec", raw="# nosec B101 CVE-2024-1234"),
        module.Suppression(file="b.py", line_no=2, kind="noqa", raw="# noqa: E501 CVE-2024-0001"),
        module.Suppression(file="c.py", line_no=3, kind="nosec", raw="# nosec B602"),
    ]

    assert module._nosec_cves(suppressions) == {"CVE-2024-1234"}


def test_active_pip_audit_ids_collects_ids_and_aliases(root, monkeypatch):
    """pip-audit JSON IDs and aliases should be normalized and returned."""
    module = _load_module(root)

    payload = """
    {
      "dependencies": [
        {"name": "pkg", "vulns": [{"id": "PYSEC-1", "aliases": ["CVE-2024-1111"]}]}
      ]
    }
    """

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout=payload, stderr=""),
    )

    assert module._active_pip_audit_ids([]) == {"PYSEC-1", "CVE-2024-1111"}


def test_active_pip_audit_ids_raises_on_unexpected_returncode(root, monkeypatch, capsys):
    """A return code outside {0, 1} should surface a RuntimeError and echo output."""
    module = _load_module(root)

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="boom-out", stderr="boom-err"),
    )

    with pytest.raises(RuntimeError, match="pip-audit execution failed"):
        module._active_pip_audit_ids([])

    captured = capsys.readouterr()
    assert "boom-out" in captured.out
    assert "boom-err" in captured.err


def test_active_pip_audit_ids_raises_on_invalid_json(root, monkeypatch):
    """Non-JSON pip-audit output should raise a descriptive RuntimeError."""
    module = _load_module(root)

    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="not-json", stderr=""),
    )

    with pytest.raises(RuntimeError, match="did not return valid JSON"):
        module._active_pip_audit_ids([])


# ---------------------------------------------------------------------------
# Scanning helpers
# ---------------------------------------------------------------------------


def test_should_skip_matches_skip_dirs(root):
    """Paths inside a skip-listed directory should be skipped."""
    module = _load_module(root)

    assert module._should_skip(Path(".venv") / "lib" / "mod.py") is True
    assert module._should_skip(Path("tests") / "test_mod.py") is True
    assert module._should_skip(Path("src") / "pkg" / "mod.py") is False


def test_is_rhiza_repo_detects_template_marker(root, tmp_path):
    """A project with .rhiza/template.yml is a consumer repo, otherwise the framework repo."""
    module = _load_module(root)

    assert module._is_rhiza_repo(tmp_path) is True

    (tmp_path / ".rhiza").mkdir()
    (tmp_path / ".rhiza" / "template.yml").write_text("upstream: x\n", encoding="utf-8")
    assert module._is_rhiza_repo(tmp_path) is False


def test_scan_file_detects_every_suppression_kind(root, tmp_path):
    """scan_file should classify each suppression family and capture its codes."""
    module = _load_module(root)

    target = tmp_path / "sample.py"
    target.write_text(
        "\n".join(
            [
                "x = 1  # noqa: E501, F401",
                "y = 2  # nosec B101",
                "z: int = 3  # type: ignore[assignment]",
                "w = 4  # pragma: no cover",
                "v = 5  # noinspection PyUnresolvedReferences",
                "ok = 6  # just a normal comment",
            ]
        ),
        encoding="utf-8",
    )

    found = {sup.kind: sup for sup in module.scan_file(target)}

    assert found["noqa"].codes == ["E501", "F401"]
    assert found["nosec"].codes == ["B101"]
    assert found["type:ignore"].codes == ["assignment"]
    assert found["no cover"].codes == []
    assert found["noinspection"].codes == ["PyUnresolvedReferences"]
    assert "just a normal comment" not in {s.raw for s in module.scan_file(target)}


def test_scan_file_returns_empty_for_unreadable_file(root, tmp_path):
    """A missing file should yield no suppressions rather than raising."""
    module = _load_module(root)

    assert module.scan_file(tmp_path / "does-not-exist.py") == []


def test_scan_file_swallows_tokenize_errors(root, tmp_path):
    """A file that fails to tokenize should be skipped without raising."""
    module = _load_module(root)

    broken = tmp_path / "broken.py"
    broken.write_text('x = "unterminated  # noqa: E501\n', encoding="utf-8")

    # Should not raise; tokenize errors are caught and the partial result returned.
    assert isinstance(module.scan_file(broken), list)


def test_count_non_empty_lines(root, tmp_path):
    """Only lines with non-whitespace content should be counted."""
    module = _load_module(root)

    target = tmp_path / "lines.py"
    target.write_text("a = 1\n\n   \nb = 2\n", encoding="utf-8")

    assert module.count_non_empty_lines(target) == 2
    assert module.count_non_empty_lines(tmp_path / "missing.py") == 0


# ---------------------------------------------------------------------------
# Grading and rendering
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("density", "expected"),
    [(0.0, "A+"), (0.5, "A"), (1.0, "B"), (2.0, "C"), (3.0, "D"), (10.0, "F")],
)
def test_compute_grade_thresholds(root, density, expected):
    """Grades should map to the documented density thresholds."""
    module = _load_module(root)

    assert module.compute_grade(density) == expected


def test_bar_renders_fixed_width(root):
    """The histogram bar is always _BAR_WIDTH wide, all-empty when max is zero."""
    module = _load_module(root)

    assert module._bar(0, 0) == "░" * module._BAR_WIDTH
    bar = module._bar(5, 10)
    assert len(bar) == module._BAR_WIDTH
    assert "█" in bar
    assert "░" in bar


# ---------------------------------------------------------------------------
# Collection
# ---------------------------------------------------------------------------


def test_collect_suppressions_includes_rhiza_dir_in_framework_repo(root, tmp_path):
    """In the framework repo (no template.yml) .rhiza/ files are scanned."""
    module = _load_module(root)

    (tmp_path / ".rhiza" / "utils").mkdir(parents=True)
    (tmp_path / "app.py").write_text("a = 1  # noqa: E501\n", encoding="utf-8")
    (tmp_path / ".rhiza" / "utils" / "helper.py").write_text("b = 2  # nosec B101\n", encoding="utf-8")

    py_files, suppressions, total_lines = module._collect_suppressions(tmp_path)

    scanned = {Path(s.file).name for s in suppressions}
    assert scanned == {"app.py", "helper.py"}
    assert total_lines == 2
    assert len(py_files) == 2


def test_collect_suppressions_skips_rhiza_dir_in_consumer_repo(root, tmp_path):
    """In a consumer repo (template.yml present) the .rhiza/ tree is excluded."""
    module = _load_module(root)

    (tmp_path / ".rhiza").mkdir()
    (tmp_path / ".rhiza" / "template.yml").write_text("upstream: x\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("a = 1  # noqa: E501\n", encoding="utf-8")
    (tmp_path / ".rhiza" / "framework.py").write_text("b = 2  # nosec B101\n", encoding="utf-8")

    _py_files, suppressions, _total = module._collect_suppressions(tmp_path)

    scanned = {Path(s.file).name for s in suppressions}
    assert scanned == {"app.py"}


def test_print_report_with_suppressions(root, capsys):
    """The report should render details, a histogram, and a grade when suppressions exist."""
    module = _load_module(root)

    suppressions = [
        module.Suppression(file="app.py", line_no=10, kind="noqa", codes=["E501"], raw="# noqa: E501"),
        module.Suppression(file="app.py", line_no=20, kind="nosec", codes=[], raw="# nosec"),
    ]
    module._print_report([Path("app.py")], suppressions, total_lines=100)

    out = strip_ansi(capsys.readouterr().out)
    assert "Suppression Audit Report" in out
    assert "app.py:10: # noqa[E501]" in out
    assert "Histogram (by suppression code):" in out
    assert "noqa[E501]" in out
    assert "Grade" in out
    assert "Suppressions    : 2" in out


def test_print_report_without_suppressions(root, capsys):
    """A clean codebase should report no suppressions and an empty histogram."""
    module = _load_module(root)

    module._print_report([Path("app.py")], [], total_lines=0)

    out = strip_ansi(capsys.readouterr().out)
    assert "No inline suppressions found." in out
    assert "(none)" in out


# ---------------------------------------------------------------------------
# Stale-CVE gate and entry point
# ---------------------------------------------------------------------------


def test_check_stale_nosec_cves_no_suppressions(root, capsys):
    """With no CVE-tagged # nosec comments the check passes without calling pip-audit."""
    module = _load_module(root)

    assert module._check_stale_nosec_cves([], []) == 0
    assert "No CVE-tagged # nosec suppressions found." in strip_ansi(capsys.readouterr().out)


def test_check_stale_nosec_cves_flags_stale(root, monkeypatch, capsys):
    """A suppressed CVE that pip-audit no longer reports is flagged as stale."""
    module = _load_module(root)

    suppressions = [module.Suppression(file="a.py", line_no=1, kind="nosec", raw="# nosec B101 CVE-2024-1234")]
    monkeypatch.setattr(module, "_active_pip_audit_ids", lambda _args: set())

    assert module._check_stale_nosec_cves(suppressions, []) == 1
    assert "Stale # nosec CVE suppressions detected:" in strip_ansi(capsys.readouterr().out)


def test_check_stale_nosec_cves_all_active(root, monkeypatch, capsys):
    """A suppressed CVE that pip-audit still reports is considered current."""
    module = _load_module(root)

    suppressions = [module.Suppression(file="a.py", line_no=1, kind="nosec", raw="# nosec B101 CVE-2024-1234")]
    monkeypatch.setattr(module, "_active_pip_audit_ids", lambda _args: {"CVE-2024-1234"})

    assert module._check_stale_nosec_cves(suppressions, []) == 0
    assert "match active pip-audit findings." in strip_ansi(capsys.readouterr().out)


def test_check_stale_nosec_cves_pip_audit_failure(root, monkeypatch, capsys):
    """A pip-audit RuntimeError should surface as exit code 2."""
    module = _load_module(root)

    suppressions = [module.Suppression(file="a.py", line_no=1, kind="nosec", raw="# nosec B101 CVE-2024-1234")]
    # A return code outside {0, 1} makes the real _active_pip_audit_ids raise,
    # which _check_stale_nosec_cves should translate into exit code 2.
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="", stderr=""),
    )

    assert module._check_stale_nosec_cves(suppressions, []) == 2
    assert "pip-audit execution failed" in strip_ansi(capsys.readouterr().out)


def test_main_reports_and_returns_zero(root, monkeypatch, tmp_path, capsys):
    """A plain run scans the working tree, prints the report, and returns 0."""
    module = _load_module(root)

    (tmp_path / "app.py").write_text("a = 1  # noqa: E501\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert module.main([]) == 0
    assert "Suppression Audit Report" in strip_ansi(capsys.readouterr().out)


def test_main_with_stale_gate_returns_one(root, monkeypatch, tmp_path, capsys):
    """The --fail-stale-nosec-cve flag fails when a suppressed CVE is no longer active."""
    module = _load_module(root)

    (tmp_path / "app.py").write_text("a = 1  # nosec B101 CVE-2024-9999\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "_active_pip_audit_ids", lambda _args: set())

    assert module.main(["--fail-stale-nosec-cve"]) == 1
    assert "Stale # nosec CVE suppressions detected:" in strip_ansi(capsys.readouterr().out)
