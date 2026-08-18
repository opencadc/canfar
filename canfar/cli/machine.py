"""Shared helpers for CLI machine output integration."""

from __future__ import annotations

from typing import Annotated, Literal

import typer

from canfar.cli import output


OutputOption = Annotated[
    Literal["json", "yaml"] | None,
    typer.Option(
        "-o",
        "--output",
        metavar="json|yaml",
        help="Emit machine-readable JSON or YAML on stdout.",
    ),
]
"""Leaf command option for selecting machine output format."""


def resolve_mode(output_format: str | None) -> output.OutputMode:
    """Resolve machine output mode from the leaf output option.

    Args:
        output_format: Requested machine output format, if any.

    Returns:
        Effective output mode for the invocation.

    Raises:
        ValueError: If the format is not supported.
    """
    if output_format is None:
        return output.OutputMode.HUMAN
    return output.OutputMode(output_format)
