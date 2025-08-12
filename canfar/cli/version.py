"""Version command for Science Platform CLI."""

from __future__ import annotations

import platform
import sys
from importlib import metadata

import typer
from rich.console import Console
from rich.table import Table

from canfar import __version__

console = Console()


def callback(
    debug: bool = typer.Option(
        default=False,
        flag_value="--debug",
        is_flag=True,
        help="Show detailed information for bug reports.",
    ),
) -> None:
    """CANFAR Python Client version information."""
    if not debug:
        # Simple version output
        console.print(f"CANFAR Python Client {__version__}")
        raise typer.Exit(0)

    # Detailed debug information
    console.print("\n[bold blue]CANFAR Python Client Debug Information[/bold blue]")

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

    console.print(table)

    # Key Dependencies
    console.print("\n[bold blue]Key Dependencies[/bold blue]")
    deps_table = Table(show_header=True, box=None)
    deps_table.add_column("Package", style="bold green", width=22)
    deps_table.add_column("Version", style="white")

    # Core dependencies that are most likely to cause issues
    key_deps = [
        "httpx",
        "typer",
        "rich",
        "pydantic",
        "cadcutils",
    ]

    for dep in key_deps:
        version_str = _get_package_version(dep)
        deps_table.add_row(dep, version_str)

    console.print(deps_table)

    # Additional information
    console.print("\n[bold blue]Additional Information[/bold blue]")
    console.print("• Repository: https://github.com/opencadc/canfar")
    console.print("• Issues: https://github.com/opencadc/canfar/issues")
    console.print("• Documentation: https://opencadc.github.io/canfar/")
    console.print("\n[dim]Please include this information when reporting bugs.[/dim]")
    raise typer.Exit(0)


version = typer.Typer(
    name="version",
    help="Show canfar client version information",
    no_args_is_help=False,
    rich_help_panel="Information Commands",
    callback=callback,
    invoke_without_command=True,
)


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
        # Check if we can find the package metadata
        dist = metadata.distribution("canfar")
        if not dist.files:
            return "unknown"

        # Check if installed in development mode
        is_development = False
        for file in dist.files:
            if str(file).endswith(".egg-link") or "site-packages" not in str(file):
                is_development = True
                break

        if is_development:
            return "development/editable"
        return "pip/wheel"  # noqa: TRY300
    except metadata.PackageNotFoundError:
        return "development (not installed)"
