"""Display utilities for Canfar CLI."""

import sys
from typing import TYPE_CHECKING, Any

import questionary
from rich.console import Console

from canfar.models.registry import Server, ServerResults

if TYPE_CHECKING:  # pragma: no cover - typing only
    from canfar.utils.vosi import Capability


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


async def capabilities(
    capabilities: list["Capability"],
) -> tuple[str, str]:
    """Display capabilities selection workflow: version first, then auth mode.

    Args:
        capabilities: Server capabilities containing version and auth information

    Returns:
        tuple[str, str]: The selected (version, auth_mode) pair

    Raises:
        SystemExit: If no capabilities are available for selection
    """
    console = Console()

    # Check if capabilities are available
    if not capabilities:
        console.print("\n[bold red]No server capabilities available.[/bold red]")
        sys.exit(1)

    # Step 1: Interactive version selection
    version_choices = _configure_version_choices(capabilities)
    if not version_choices:
        console.print("\n[bold red]No versions available for selection.[/bold red]")
        sys.exit(1)

    try:
        selected_capability: dict[str, Any] | None = await questionary.select(
            "Select a Server Version:",
            choices=version_choices,
            style=_get_selection_style(),
        ).ask_async()
    except KeyboardInterrupt:
        sys.exit(0)

    if selected_capability is None:
        sys.exit(0)

    # Step 2: Auth mode selection
    auth_modes = selected_capability.get("auth_modes", [])
    if not auth_modes:
        console.print(
            "\n[bold red]No authentication modes available for selected "
            "version.[/bold red]"
        )
        sys.exit(1)

    # Interactive auth selection
    auth_choices = _configure_auth_choices(auth_modes)
    if not auth_choices:
        console.print(
            "\n[bold red]No authentication modes available for selection.[/bold red]"
        )
        sys.exit(1)

    try:
        selected_auth: str | None = await questionary.select(
            "Select an Auth Mode:",
            choices=auth_choices,
            style=_get_selection_style(),
        ).ask_async()
    except KeyboardInterrupt:
        sys.exit(0)

    if selected_auth is None:
        sys.exit(0)

    version = selected_capability.get("version", "") or ""
    auth = selected_auth or ""
    return version, auth


def _configure_version_choices(
    capabilities: list["Capability"],
) -> list[questionary.Choice]:
    """Configure choices for version selection with formatting.

    Args:
        capabilities: List of capability entries.

    Returns:
        list[questionary.Choice]: List of choices for questionary.
    """
    choices: list[questionary.Choice] = []

    # Calculate maximum widths for alignment
    if not capabilities:
        return choices

    max_version_width = max(
        len(cap.get("version") or "Unknown") for cap in capabilities
    )
    max_baseurl_width = max(len(cap.get("baseurl", "")) for cap in capabilities)

    for cap in capabilities:
        # Format version and baseurl with padding for alignment
        version = (cap.get("version") or "Unknown").ljust(max_version_width)
        baseurl = cap.get("baseurl", "").ljust(max_baseurl_width)
        auth_modes = ", ".join(cap.get("auth_modes", []))

        # Create choice text with consistent spacing
        choice = f"🔧 {version} {baseurl} [{auth_modes}]"

        choices.append(questionary.Choice(title=choice, value=cap))

    return choices


def _configure_auth_choices(
    auth_modes: list[str],
) -> list[questionary.Choice]:
    """Configure choices for authentication mode selection with formatting.

    Args:
        auth_modes: List of available authentication modes.

    Returns:
        list[questionary.Choice]: List of choices for questionary.
    """
    choices: list[questionary.Choice] = []

    # Auth mode descriptions for better UX
    auth_descriptions = {
        "x509": "TLS Certificate",
        "oidc": "OpenID Connect",
    }

    for mode in auth_modes:
        # Get description or use the mode name as fallback
        description = auth_descriptions.get(mode, f"{mode.upper()} Authentication")

        # Create choice text with icon and description
        choice = f"🔐 {mode.upper()} - {description}"

        choices.append(questionary.Choice(title=choice, value=mode))

    return choices


def _get_selection_style() -> questionary.Style:
    """Get consistent styling for questionary selections.

    Returns:
        questionary.Style: Consistent style configuration.
    """
    return questionary.Style(
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
    )
