"""Interactive CLI prompts for CANFAR login and selection flows."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from rich.markup import escape
from rich.prompt import IntPrompt

from canfar.utils.console import get_console

if TYPE_CHECKING:
    from canfar.idp import IdpInfo
    from canfar.models.http import Server


def choose(title: str, labels: list[str]) -> int:
    """Print numbered choices and return the index of the one the user picks.

    Args:
        title: Question shown above the choices.
        labels: One label per choice, in display order.

    Returns:
        Zero-based index of the selected label.

    Raises:
        SystemExit: When the user cancels the prompt.
    """
    console = get_console()
    console.print(f"[bold]{escape(title)}[/bold]")
    for number, label in enumerate(labels, start=1):
        console.print(f"  {number}. {escape(label)}")
    numbers = [str(number) for number in range(1, len(labels) + 1)]
    try:
        return IntPrompt.ask("Number", choices=numbers, console=console) - 1
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)


def select_idp(idps: list[IdpInfo]) -> str:
    """Prompt the user to choose a built-in Identity Provider.

    Args:
        idps: Built-in Identity Provider catalog entries.

    Returns:
        Canonical IDP key selected by the user.

    Raises:
        SystemExit: When the user cancels the prompt.
    """
    labels = [f"{idp.name} ({idp.key})" for idp in idps]
    return idps[choose("Select an Identity Provider", labels)].key


def select_server(servers: list[Server]) -> Server:
    """Prompt the user to choose a Science Platform Server.

    Args:
        servers: Known servers scoped to the active Identity Provider.

    Returns:
        Selected server record.

    Raises:
        SystemExit: When the user cancels the prompt or no servers exist.
    """
    servers = [server for server in servers if server.uri is not None]
    if not servers:
        sys.exit(1)
    if len(servers) == 1:
        return servers[0]

    labels = [f"{server.name or server.uri} ({server.uri})" for server in servers]
    return servers[choose("Select a Science Platform Server", labels)]
