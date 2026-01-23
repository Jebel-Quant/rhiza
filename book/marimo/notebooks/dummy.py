"""Dummy notebook to test-cover and give an example of referencing this package as editable."""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo==0.18.4",
#     "rhiza",
# ]
# [tool.uv.sources]
# rhiza = { path = "../../../", editable = true }
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    from hello.hello import print_hello

    print_hello("World")
    return


if __name__ == "__main__":
    app.run()
