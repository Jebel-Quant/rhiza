"""Shared handling of README fence flags.

``SKIP_FLAG`` and :func:`should_skip` were deliberately duplicated across
``test_readme.py`` and ``test_readme_validation.py`` while the suite was delivered by
file-copy: the two modules shipped in different bundles, a Rust project received one and
not the other, and a shared helper would have needed a third bundle-owned home. Packaging
the suite removes that constraint — one distribution carries every module, so the helper
has somewhere to live.
"""

from __future__ import annotations

# Flag marking a fence as intentionally excluded from the README gates. Usage: add it
# after the language identifier on the opening fence line, e.g. ```bash +RHIZA_SKIP
SKIP_FLAG = "+RHIZA_SKIP"


def should_skip(flags: str) -> bool:
    """Report whether a fence's flags mark it as intentionally excluded.

    Args:
        flags: Text following the language identifier on the opening fence line.

    Returns:
        bool: True when the block carries :data:`SKIP_FLAG`.
    """
    return SKIP_FLAG in flags
