"""Sample Typer application used by the plugin loader tests."""

from __future__ import annotations

import typer

app = typer.Typer(invoke_without_command=True, no_args_is_help=False)


@app.callback()
def main() -> None:
    """Reply so the loader test can see the plugin ran."""
    typer.echo("plugin-ok")
