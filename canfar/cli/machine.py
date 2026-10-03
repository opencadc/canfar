"""Shared option declarations for CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

import typer

from canfar.cli import output

if TYPE_CHECKING:
    from pydantic import BaseModel

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


def maximum(model: type[BaseModel], field: str) -> int:
    """Return the largest value ``model`` accepts for ``field``, for option ranges.

    Args:
        model: Pydantic model that declares the bound.
        field: Field with an ``le`` constraint.

    Returns:
        The field's inclusive upper bound.
    """
    metadata = model.model_fields[field].metadata
    return next(rule.le for rule in metadata if hasattr(rule, "le"))
