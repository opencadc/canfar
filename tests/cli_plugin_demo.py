"""Sample Typer application used by the plugin loader tests."""

from __future__ import annotations

from types import SimpleNamespace

import typer

app = typer.Typer(invoke_without_command=True, no_args_is_help=False)
commands = SimpleNamespace(app=app)


@app.callback()
def main() -> None:
    """Reply so the loader test can see the plugin ran."""
    typer.echo("plugin-ok")


@app.command()
def hello() -> None:
    """Greet the user."""
    typer.echo("hello")
