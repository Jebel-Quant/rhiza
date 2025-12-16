"""Rhiza command-line interface (CLI).

This module defines the Typer application entry points exposed by Rhiza.
Commands are thin wrappers around implementations in `rhiza.commands.*`.
"""

from pathlib import Path

import typer

from rhiza.commands.hello import hello as hello_cmd
from rhiza.commands.inject import inject as inject_cmd

app = typer.Typer(help="rhiza — configuration materialization tools")


@app.command()
def hello():
    """Sanity check command."""
    hello_cmd()


@app.command()
def inject(
    target: Path = typer.Argument(
        default=Path("."),  # default to current directory
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Target git repository (defaults to current directory)",
    ),
    branch: str = typer.Option("main", "--branch", "-b", help="Rhiza branch to use"),
    force: bool = typer.Option(False, "--force", "-y", help="Overwrite existing files"),
):
    """Inject Rhiza configuration into a target repository.

    Parameters
    ----------
    target:
        Path to the target Git repository directory. Defaults to the
        current working directory.
    branch:
        Name of the Rhiza branch to use when sourcing templates.
    force:
        If True, overwrite existing files without prompting.
    """
    inject_cmd(target, branch, force)
