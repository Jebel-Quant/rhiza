# Blueprint Tests

> **⚠️ These tests are blueprints for downstream repositories, not the Rhiza project's own test suite.**

This directory contains example test scaffolding that is synced into downstream projects via Rhiza.
The tests here serve as a **starting point** that downstream maintainers are expected to replace with
their own meaningful tests.

## What is in this directory

| Directory | Purpose |
|-----------|---------|
| `benchmarks/` | Example benchmark tests using `pytest-benchmark` — replace with benchmarks for your own code |
| `property/` | Example property-based tests using `Hypothesis` — replace with property tests for your own logic |
| `stress/` | Example stress/concurrency tests — replace with stress tests for your own system |

None of the tests in this directory test Rhiza-specific logic.

## Rhiza's own tests

The comprehensive test suite for the Rhiza project itself lives in **`.rhiza/tests/`**.
Those tests cover:

- **`structure/`** — repository layout and configuration structure
- **`api/`** — Makefile target validation
- **`integration/`** — end-to-end workflows in sandboxed git repositories
- **`sync/`** — template synchronisation and content validation
- **`utils/`** — test infrastructure and utility code
- **`deps/`** — dependency health validation
- **`stress/`** — Rhiza-specific operations under load

See [`.rhiza/tests/README.md`](../.rhiza/tests/README.md) for full documentation.
