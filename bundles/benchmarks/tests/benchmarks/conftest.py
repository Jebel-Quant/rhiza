"""Pytest configuration for the benchmark tests.

Shared fixtures for your benchmarks belong here. Keep them to what the ``benchmark`` gate
itself provides: it runs pytest with ``pytest-benchmark`` and ``pygal``, and nothing else.
A fixture from another plugin may or may not be present, depending on what the project's
own environment happens to carry.

For *hooks* that is not a soft warning but a hard failure, which is why this file used to
break the gate it ships with. It defined ``pytest_html_report_title``, a ``pytest-html``
hook -- and the gate injects no ``pytest-html``, because it writes a histogram and a JSON
file rather than an HTML report. pluggy validates hook *names* when collection starts, so
an implementation of a hook that no installed plugin declares is not ignored: pytest raises
``PluginValidationError: unknown hook 'pytest_html_report_title'`` as an INTERNALERROR and
exits 3 before a single benchmark is collected. Any consumer of this bundle whose
environment did not happen to carry pytest-html therefore had a ``make benchmark`` that
could not run -- and no ``make book`` either, since ``book`` needs ``benchmark``.

Security Notes:
- S101 (assert usage): Asserts are the standard way to validate test conditions in pytest.
  They provide clear test failure messages and are expected in test code.
"""
