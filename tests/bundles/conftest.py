"""Fixtures shared by the bundle-content suites.

``bundle_names`` moved here from ``test_bundle_content_validity.py`` when that module was
split (#1514): three sibling suites now need it, and a fixture imported from another test
module is a fixture that silently stops being applied the moment the import is tidied
away.

Security: this conftest takes no security exceptions. Unlike ``tests/conftest.py`` and
``tests/integration/conftest.py``, it spawns no subprocess and needs no ``S603``/``S607``
suppressions — it only reads ``.rhiza/template-bundles.yml`` from the repository tree. The
note is here because ``tests/security/test_security_patterns.py`` requires every conftest
to state its posture, and "none required" is a posture worth stating explicitly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.bundles._content import _load_bundle_names


@pytest.fixture(scope="module")
def bundle_names(root: Path) -> list[str]:
    """Return all bundle names defined in template-bundles.yml."""
    return _load_bundle_names(root)
