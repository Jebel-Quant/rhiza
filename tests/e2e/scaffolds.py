"""The project files each language layer's gates are run against.

A bundle sync delivers infrastructure — a Makefile, lint configs, a pre-commit
config — but no code. So an end-to-end run needs the other half: the smallest
project that a *correct* layer should pass every gate on. That project is what
these dictionaries hold, one per layer, keyed by path relative to the project root.

They are deliberately written to be exactly gate-clean and no more:

* documented down to the last public item, because `docs-coverage` is
  interrogate at 100% / ``-D missing_docs`` / revive's ``exported`` rule
* fully covered by one test, because the coverage floor is 90%
* formatter-clean as written (tabs in Go, rustfmt spacing in Rust), because
  `fmt` runs the formatters through pre-commit and fails on a diff
* annotated and licensed, because `typecheck` is mypy ``--strict`` and the
  licence gates read ``[project].license`` / ``[package].license``

That tightness is the point: anything a gate would flag is a deliberate signal,
so when e2e goes red it is the template that regressed, not the fixture.

Kept as string constants rather than files on disk so the mother repo's own ruff,
interrogate and mypy runs do not lint a Python package that is meant to be a
downstream project's, and so each layer's scaffold reads as one unit.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

# Every scaffold carries one: the pointer file `check-rhiza-config` (a pre-commit
# hook from rhiza-hooks that `fmt` runs) expects in a rhiza-managed repo. No
# bundle ships it, because it is the consumer's own declaration of what it synced.
_TEMPLATE_YML = """\
repository: jebel-quant/rhiza
ref: v1.2.5
profiles:
  - {profile}
"""

# No ```python fence, and one ```bash fence, for two different reasons.
#
# No Python: `rhiza-test` runs the shipped test_readme_validation.py, which executes
# every ```python block and diffs it against the following ```result block. An empty
# set of blocks passes that trivially, which keeps the README about the scaffold
# rather than about satisfying a test — and on a Rust or Go scaffold there is no
# Python to demonstrate anyway.
#
# One bash fence, because core's test_readme.py syntax-checks them with `bash -n` for
# every layer (#1472), and a README with no fence at all would pass that trivially too
# — the exact vacuum #1469 was about. The block is never executed, so naming real
# targets here costs nothing and keeps the check honest.
_README = """\
# demo

A minimal {language} project assembled by rhiza's end-to-end suite.

It exists to prove that a freshly synced project passes every gate the
`{layer}` language layer ships, with no hand-holding beyond the code below.

```bash
make install
make all
```
"""


def _readme(language: str, layer: str) -> str:
    """Return the scaffold README for a layer.

    Args:
        language: Human-readable language name, e.g. ``"Python"``.
        layer: The bundle that ships the layer, e.g. ``"python-core"``.

    Returns:
        Markdown that passes markdownlint with MD013 disabled.
    """
    return _README.format(language=language, layer=layer)


def template_yml(profile: str) -> str:
    """Return a `.rhiza/template.yml` naming the profile the scaffold assembles.

    Written by `harness.assemble` from the layer's own ``profile`` field rather than
    being listed in the dictionaries below, so the profile a scaffold claims and the
    bundle list it is actually built from cannot drift apart.

    Args:
        profile: The profile in `.rhiza/template-bundles.yml` this scaffold mirrors.

    Returns:
        YAML for the repo-owned rhiza pointer file.
    """
    return _TEMPLATE_YML.format(profile=profile)


# ---------------------------------------------------------------------------
# Python (bundle: python-core, plus tests for pytest/coverage/typecheck)
# ---------------------------------------------------------------------------

# requires-python tracks bundles/python-core/.python-version: the
# check-python-version-consistency pre-commit hook reconciles the two, so a
# scaffold that disagrees with the shipped interpreter fails `fmt`.
#
# hatchling with an explicit wheel target rather than a bare [project] table:
# without a build system uv treats the project as virtual and never installs it,
# so `import demo` — and with it the coverage measurement of src/ — would fail.
_PYTHON_PYPROJECT = """\
[project]
name = "demo"
version = "0.1.0"
description = "A minimal project proving the python-core layer's gates pass on a fresh sync."
readme = "README.md"
requires-python = ">=3.12"
license = "MIT"
authors = [
  { name = "Rhiza End-To-End Suite" }
]
classifiers = [
    "Programming Language :: Python :: 3.12",
]
dependencies = []

[project.urls]
Homepage = "https://github.com/jebel-quant/rhiza"
Repository = "https://github.com/jebel-quant/rhiza"

[dependency-groups]
test = [
    "pytest>=9,<10",
]
lint = [
    "ruff>=0.16,<1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/demo"]

# The version config a synced Python repo has to declare for itself (#1453). The
# python-core layer ships none: pyproject.toml is one of the four filenames
# bump-my-version searches, so a table here rewrites [project].version natively,
# whereas a synced .bumpversion.toml would shadow it and a block in .rhiza/ would
# never be read at all. Three keys and no current_version is the whole config —
# `make rhiza-test` fails without it.
[tool.bumpversion]
allow_dirty = false
# /rhiza:release commits and tags itself so the changelog lands in the bump commit.
commit = false
tag = false
"""

_PYTHON_INIT = '"""A minimal package whose public surface is one greeting helper."""\n'

# The doctest is load-bearing: `make rhiza-test` runs the shipped
# test_docstrings.py, which discovers packages under SOURCE_FOLDER and skips when
# no module has any doctests. With one here, that self-test actually asserts.
_PYTHON_GREETING = '''\
"""Build greetings, the one behaviour this scaffold ships."""

from __future__ import annotations


def greet(name: str) -> str:
    """Return a greeting addressed to ``name``.

    Args:
        name: Who to greet.

    Returns:
        The greeting.

    Examples:
        >>> greet("rhiza")
        'Hello, rhiza!'
    """
    return f"Hello, {name}!"
'''

_PYTHON_TEST = '''\
"""Tests for the greeting helper, covering every line of src/."""

from demo.greeting import greet


def test_greet_addresses_the_caller_by_name():
    """greet() interpolates the name it is given."""
    assert greet("rhiza") == "Hello, rhiza!"
'''

PYTHON_FILES: dict[str, str] = {
    "pyproject.toml": _PYTHON_PYPROJECT,
    "README.md": _readme("Python", "python-core"),
    "src/demo/__init__.py": _PYTHON_INIT,
    "src/demo/greeting.py": _PYTHON_GREETING,
    "tests/test_greeting.py": _PYTHON_TEST,
}

# ---------------------------------------------------------------------------
# Rust (bundle: rust-core)
# ---------------------------------------------------------------------------

# `license` is not decoration: `cargo deny check licenses` walks the whole graph
# including the root crate, so an unlicensed scaffold fails the licence gate on
# itself rather than on a dependency.
_RUST_CARGO_TOML = """\
[package]
name = "demo"
version = "0.1.0"
edition = "2021"
description = "A minimal crate proving the rust-core layer's gates pass on a fresh sync."
license = "MIT"

[dependencies]
"""

# Formatted as rustfmt would leave it (4-space indent, max_width 100 from
# rustfmt.toml): `fmt` runs `cargo fmt --all --` through pre-commit, which fails
# the hook when it rewrites a file.
#
# The `# Examples` block is a doctest, which nextest does not run — it is what
# the layer's separate `cargo test --doc` line exists for, so `make test` only
# proves both halves when there is a doctest to run.
_RUST_LIB = """\
//! A minimal crate whose public surface is one greeting helper.

/// Returns a greeting addressed to `name`.
///
/// # Examples
///
/// ```
/// assert_eq!(demo::greet("rhiza"), "Hello, rhiza!");
/// ```
pub fn greet(name: &str) -> String {
    format!("Hello, {name}!")
}

#[cfg(test)]
mod tests {
    use super::greet;

    #[test]
    fn greets_the_caller_by_name() {
        assert_eq!(greet("rhiza"), "Hello, rhiza!");
    }
}
"""

RUST_FILES: dict[str, str] = {
    "Cargo.toml": _RUST_CARGO_TOML,
    "README.md": _readme("Rust", "rust-core"),
    "src/lib.rs": _RUST_LIB,
}

# ---------------------------------------------------------------------------
# Go (bundle: go-core)
# ---------------------------------------------------------------------------

# `go 1.23` is the floor the layer's own gates need, not a preference:
# `go mod tidy -diff` — which `make deps` is — landed in 1.23. A newer toolchain
# on the machine is fine; go.mod's directive only sets the language version.
_GO_MOD = """\
module example.com/demo

go 1.23
"""

# Tab-indented, single-line imports, doc comments starting with the identifier
# name: `fmt` runs gofmt through pre-commit and `docs-coverage` runs revive's
# `exported` rule, so both the layout and the comment wording are gates here.
#
# "behavior", not "behaviour": .golangci.yml enables misspell with `locale: US`, so
# `typecheck` fails a British spelling in a comment. Found by running the gate —
# the sibling scaffolds spell it the other way and nothing complains, because
# neither ruff nor clippy checks spelling.
_GO_GREETING = """\
// Package greeting builds greetings, the one behavior this scaffold ships.
package greeting

import "fmt"

// Greet returns a greeting addressed to name.
func Greet(name string) string {
\treturn fmt.Sprintf("Hello, %s!", name)
}
"""

_GO_GREETING_TEST = """\
package greeting

import "testing"

func TestGreet(t *testing.T) {
\tt.Parallel()

\tif got, want := Greet("rhiza"), "Hello, rhiza!"; got != want {
\t\tt.Fatalf("Greet(%q) = %q, want %q", "rhiza", got, want)
\t}
}
"""

GO_FILES: dict[str, str] = {
    "go.mod": _GO_MOD,
    "README.md": _readme("Go", "go-core"),
    "greeting/greeting.go": _GO_GREETING,
    "greeting/greeting_test.go": _GO_GREETING_TEST,
}
