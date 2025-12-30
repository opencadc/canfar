"""CLI command to list CANFAR images."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, get_args

import click
import typer
from rich import box
from rich.table import Table
from rich.text import Text

from canfar.images import Images
from canfar.models.types import Kind
from canfar.utils.console import console

if TYPE_CHECKING:
    from canfar.models.containers import Image

image = typer.Typer(
    name="image",
    no_args_is_help=True,
)

KIND_ORDER: list[str] = list(get_args(Kind))
KIND_STYLES: dict[str, str] = {
    "desktop": "#2aa198",
    "notebook": "#859900",
    "carta": "#6c71c4",
    "headless": "#268bd2",
    "firefly": "#6c71c4",
    "desktop-app": "#6c71c4",
    "contributed": "#b58900",
}


def _split_server(image_id: str) -> tuple[str, str]:
    server, _, remainder = image_id.partition("/")
    if not remainder:
        return "unknown", image_id
    return server, remainder


def _short_digest(digest: str | None) -> str:
    if not digest:
        return "unknown"
    _, _, remainder = digest.partition(":")
    if remainder:
        digest = remainder
    return digest[:12]


def _sort_kinds(kinds: list[str]) -> list[str]:
    rank = {kind: index for index, kind in enumerate(KIND_ORDER)}
    return sorted(set(kinds), key=lambda kind: (rank.get(kind, len(rank)), kind))


def _format_kinds(kinds: list[str]) -> Text:
    if not kinds:
        return Text("unknown")
    text = Text()
    for kind in _sort_kinds(kinds):
        style = KIND_STYLES.get(kind, "white on #dc322f")
        text.append(f" {kind} ", style=style)
        text.append(" ")
    return text


@image.command("ls")
def ls(
    kind: Annotated[
        Kind | None,
        typer.Option(
            "--kind",
            "-k",
            click_type=click.Choice(list(get_args(Kind)), case_sensitive=True),
            metavar="|".join(get_args(Kind)),
            help="Filter by image kind.",
        ),
    ] = None,
) -> None:
    """List available images."""
    payload: list[Image] = Images().details()
    images = [image for image in payload if not kind or kind in image.types]
    if not images:
        console.print("[yellow]No images found.[/yellow]")
        return

    server, _ = _split_server(images[0].id)
    table = Table(
        title=f"CANFAR Registry Server: {server}",
        box=box.SIMPLE,
        header_style="bold cyan",
    )
    table.add_column("IMAGE", style="cyan")
    table.add_column("ID", style="magenta")
    table.add_column("KIND", style="green")

    for image in images:
        _, image_id = _split_server(image.id)
        short_digest = _short_digest(image.digest)
        kinds = _format_kinds(image.types)
        table.add_row(image_id, short_digest, kinds)

    console.print(table)
