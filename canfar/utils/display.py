"""Display utilities for Canfar CLI."""

import sys

import questionary
from rich.console import Console

from canfar.models.registry import Server, ServerResults


async def servers(
    results: ServerResults,
    show_dead: bool = False,
    show_details: bool = False,
) -> Server:
    """Display discovery results and require interactive selection.

    Args:
        results: Discovery results containing endpoint information
        show_dead: Whether to show inactive endpoints. (default: False)
        show_details: Whether to show detailed URI and URL information (default: False)

    Returns:
        ServerInfo: The selected server info

    Raises:
        SystemExit: If no endpoints are available for selection
    """
    console = Console()

    alive: list[Server] = [
        endpoint for endpoint in results.endpoints if endpoint.status == 200
    ]
    dead: list[Server] = [
        endpoint for endpoint in results.endpoints if endpoint.status != 200
    ]

    # Check if endpoints are available
    if not alive and not dead:
        console.print("\n[bold red]No servers available.[/bold red]")
        sys.exit(1)

    # Create choices for questionary with equal length formatting
    choices: list[questionary.Choice] = configure_server_choices(
        show_dead, show_details, alive, dead
    )

    # Check if any choices are available for selection
    if not choices:
        console.print("\n[bold red]No servers available for selection.[/bold red]")
        sys.exit(1)

    # Use questionary to select an endpoint
    try:
        selection: Server | None = await questionary.select(
            "Select a Canfar Server:",
            choices=choices,
            style=questionary.Style(
                [
                    ("question", "bold"),
                    ("answer", "fg:#ff9d00 bold"),
                    ("pointer", "fg:#ff9d00 bold"),
                    ("highlighted", "fg:#ff9d00 bold"),
                    ("selected", "fg:#cc5454"),
                    ("separator", "fg:#cc5454"),
                    ("instruction", ""),
                    ("text", ""),
                    ("disabled", "fg:#858585 italic"),
                ]
            ),
        ).ask_async()
    except KeyboardInterrupt:
        sys.exit(0)
    else:
        if selection is None:
            # User cancelled with Ctrl+C
            sys.exit(0)
        return selection


def configure_server_choices(
    show_dead: bool,
    show_details: bool,
    alive: list[Server],
    dead: list[Server],
) -> list[questionary.Choice]:
    """Configure choices for questionary with equal length formatting.

    Args:
        show_dead: Whether to show inactive endpoints.
        show_details: Whether to show detailed URI and URL information.
        alive: List of alive endpoints.
        dead: List of dead endpoints.

    Returns:
        list[questionary.Choice]: List of choices for questionary.
    """
    choices: list[questionary.Choice] = []
    available: list[Server] = alive
    if show_dead:
        available.extend(dead)

    # Calculate maximum widths for alignment
    if not available:
        return choices

    max_name_width = max(len(endpoint.name or "Unknown") for endpoint in available)
    max_registry_width = max(len(endpoint.registry) for endpoint in available)

    max_uri_width = 0
    if show_details:
        max_uri_width = max(len(endpoint.uri) for endpoint in available)

    for endpoint in available:
        # Determine status indicator
        indicator = "🔴" if endpoint.status is None else "🟢"

        # Format name and registry with padding for alignment
        name = (endpoint.name or "Unknown").ljust(max_name_width)
        registry = endpoint.registry.ljust(max_registry_width)

        # Create choice text with consistent spacing
        choice = f"{indicator} {name} {registry}"

        # Add detailed info if requested with alignment
        if show_details:
            uri = endpoint.uri.ljust(max_uri_width)
            choice += f" {uri} {endpoint.url}"

        choices.append(questionary.Choice(title=choice, value=endpoint))
    return choices
