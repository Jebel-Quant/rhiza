"""Marimo app notebook demonstrating the config.add function.

This module is an auto-generated Marimo notebook. It imports the add helper
from the config package and evaluates a few simple cells. The module is used
for documentation/book integration and can be launched with `python -m marimo`
or by running this file directly.
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "rhiza",
# ]
#
# [tool.uv.sources]
# rhiza = { path = "../..", editable = true }
# ///

import marimo

__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell
def _():
    from rhiza.commands.hello import hello

    hello()
    return


if __name__ == "__main__":
    app.run()
