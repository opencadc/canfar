"""Version command for Science Platform CLI."""

from __future__ import annotations

import platform
import sys
from importlib import metadata
from typing import Annotated

import typer
from rich.table import Table

from canfar import __version__
from canfar.utils.console import emit_cli_active_server_banner, get_console


def callback(
    debug: Annotated[
        bool, typer.Option("--debug", help="Show detailed information for bug reports.")
    ] = False,
) -> None:
    """CANFAR Python Client version information."""
    emit_cli_active_server_banner()
    if not debug:
        # Simple version output
        get_console().print(f"CANFAR Python Client {__version__}")
        raise typer.Exit(0)

    # Detailed debug information
    get_console().print(
        "\n[bold blue]CANFAR Python Client Debug Information[/bold blue]"
    )

    # Client Information
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="bold green", width=22)
    table.add_column("Value", style="white")

    # Client version and git info
    table.add_row("Client Version", __version__)
    installation_info = _get_installation_info()
    table.add_row("Source", installation_info)

    # Python information
    table.add_row("", "")  # Empty row for spacing
    table.add_row("Python Version", platform.python_version())
    table.add_row("Python Executable", sys.executable)
    table.add_row("Python Impl", platform.python_implementation())

    # System information
    table.add_row("", "")  # Empty row for spacing
    table.add_row("Operating System", platform.system())
    table.add_row("OS Version:", platform.release())
    table.add_row("Architecture", platform.machine())
    table.add_row("Platform", platform.platform())

    get_console().print(table)

    # Key Dependencies
    get_console().print("\n[bold blue]Key Dependencies[/bold blue]")
    deps_table = Table(show_header=True, box=None)
    deps_table.add_column("Package", style="bold green", width=22)
    deps_table.add_column("Version", style="white")

    # Core dependencies that are most likely to cause issues
    key_deps = [
        "httpx2",
        "typer",
        "rich",
        "pydantic",
    ]

    for dep in key_deps:
        version_str = _get_package_version(dep)
        deps_table.add_row(dep, version_str)

    get_console().print(deps_table)

    # Additional information
    get_console().print("\n[bold blue]Additional Information[/bold blue]")
    get_console().print("• Repository: https://github.com/opencadc/canfar")
    get_console().print("• Issues: https://github.com/opencadc/canfar/issues")
    get_console().print("• Documentation: https://opencadc.github.io/canfar/")
    get_console().print(
        "\n[dim]Please include this information when reporting bugs.[/dim]"
    )
    raise typer.Exit(0)


def _get_package_version(name: str) -> str:
    """Get version of an installed package.

    Args:
        name (str): Name of the package to check.

    Returns:
        str: Package version or 'not installed'.
    """
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "not installed"


def _get_installation_info() -> str:
    """Get information about how canfar was installed.

    Returns:
        str: Installation method information.
    """
    try:
        dist = metadata.distribution("canfar")
    except metadata.PackageNotFoundError:
        return "development (not installed)"
    if not dist.files:
        return "unknown"
    development = any(
        str(file).endswith(".egg-link") or "site-packages" not in str(file)
        for file in dist.files
    )
    return "development/editable" if development else "pip/wheel"
