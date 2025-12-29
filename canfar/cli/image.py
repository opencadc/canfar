"""CLI command to list CANFAR images."""

from __future__ import annotations

from typing import Annotated

import typer
from rich import box
from rich.table import Table

from canfar.images import Images
from canfar.utils.console import console

image = typer.Typer(
    name="image",
    no_args_is_help=True,
)


@image.command("ls")
def ls(
    image_filter: Annotated[
        str | None,
        typer.Option(
            "--filter",
            "-f",
            help="Filter by image kind.",
        ),
    ] = None,
) -> None:
    """List available images."""
    images = Images().fetch(kind=image_filter)

    table = Table(title="CANFAR Images", box=box.SIMPLE, header_style="bold cyan")
    table.add_column("IMAGE", style="cyan")
    for image_id in images:
        table.add_row(image_id)

    console.print(table)
