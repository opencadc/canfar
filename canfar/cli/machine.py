"""Shared helpers for CLI machine output integration."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

import typer

from canfar.cli import output


class OutputFormat(str, Enum):
    """Machine output formats accepted by leaf commands."""

    JSON = "json"
    YAML = "yaml"


OutputOption = Annotated[
    OutputFormat | None,
    typer.Option(
        "-o",
        "--output",
        metavar="json|yaml",
        help="Emit machine-readable JSON or YAML on stdout.",
    ),
]
"""Leaf command option for selecting machine output format."""


def resolve_mode(output_format: OutputFormat | str | None) -> output.OutputMode:
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
    value = (
        output_format.value
        if isinstance(output_format, OutputFormat)
        else output_format
    )
    if value == "json":
        return output.OutputMode.JSON
    if value == "yaml":
        return output.OutputMode.YAML
    message = f"Unsupported output format: {value}"
    raise ValueError(message)
