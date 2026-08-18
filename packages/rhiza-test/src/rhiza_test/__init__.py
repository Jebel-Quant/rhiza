"""Rhiza's conformance suite, packaged so every managed repo runs one shared copy.

The modules under :mod:`rhiza_test.suite` used to be copied into each repo as
``.rhiza/tests/``. They are pytest modules executed *against* the repository the
command is invoked from, not an importable API — :mod:`rhiza_test.__main__` points
pytest at them and lets the ``root`` fixture discover the repo under test.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
