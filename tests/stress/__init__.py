"""Stress/load tests for Rhiza.

This package contains stress and load tests that exercise the system under high load.
These tests are marked with the 'stress' pytest marker and can be run separately from
the regular test suite.

Run stress tests only:
    pytest -m stress

Skip stress tests:
    pytest -m "not stress"
"""
