"""Shared helpers for CLI machine output integration."""

from __future__ import annotations

from typing import Annotated

import typer

from canfar.cli import output

JsonOption = Annotated[
    bool,
    typer.Option("--json", help="Emit machine-readable JSON on stdout."),
]
"""Leaf command flag for JSON machine output."""

YamlOption = Annotated[
    bool,
    typer.Option("--yaml", help="Emit machine-readable YAML on stdout."),
]
"""Leaf command flag for YAML machine output."""


def resolve_mode(json_output: bool, yaml_output: bool) -> output.OutputMode:
    """Resolve machine output mode from leaf command flags.

    Args:
        json_output: Whether ``--json`` was supplied.
        yaml_output: Whether ``--yaml`` was supplied.

    Returns:
        Effective output mode for the invocation.

    Raises:
        typer.Exit: Exit code 2 when both machine flags are supplied.
    """
    if json_output and yaml_output:
        typer.echo(
            "Conflicting machine output flags: use only one of --json or --yaml.",
            err=True,
        )
        raise typer.Exit(output.OUTPUT_CONFLICT_EXIT_CODE)
    if json_output:
        return output.OutputMode.JSON
    if yaml_output:
        return output.OutputMode.YAML
    return output.OutputMode.HUMAN
