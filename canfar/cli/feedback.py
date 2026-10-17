"""Find the public feedback routes without loading credentials or configuration."""

import typer


def callback() -> None:
    """Print the GitHub chooser for help, feedback, and problem reports."""
    typer.echo("https://github.com/opencadc/canfar/issues/new/choose")
