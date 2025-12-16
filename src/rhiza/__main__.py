"""Rhiza module entry point.

This module allows running the Rhiza CLI with `python -m rhiza` by
delegating execution to the Typer application defined in `rhiza.cli`.
"""

from rhiza.cli import app

if __name__ == "__main__":
    app()
