"""Console-script entry point for ``rhiza-test``.

Runs the packaged suite against the *current working directory's* repository. The
suite lives inside the installed package, so pytest is given an explicit rootdir:
without it pytest would infer one from the suite's own location in site-packages and
resolve the consuming repo's ``pytest.ini`` not at all.
"""

from __future__ import annotations

import pathlib
import sys

import pytest


def main() -> int:
    """Run the packaged conformance suite against the current repository.

    Returns:
        int: The pytest exit code, suitable for :func:`sys.exit`.
    """
    suite = pathlib.Path(__file__).parent / "suite"
    argv = [str(suite), "--rootdir", str(pathlib.Path.cwd()), "-p", "no:cacheprovider"]
    return int(pytest.main([*argv, *sys.argv[1:]]))


if __name__ == "__main__":
    sys.exit(main())
