"""Interactive CLI prompts for CANFAR login and selection flows."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import questionary

if TYPE_CHECKING:
    from canfar.idp import IdpInfo
    from canfar.models.http import Server


def _get_selection_style() -> questionary.Style:
    """Return the shared style for interactive CLI selections."""
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


def select_idp(idps: list[IdpInfo]) -> str:
    """Prompt the user to choose a built-in Identity Provider.

    Args:
        idps: Built-in Identity Provider catalog entries.

    Returns:
        Canonical IDP key selected by the user.

    Raises:
        SystemExit: When the user cancels the prompt.
    """
    choices = [
        questionary.Choice(
            title=f"{idp.name} ({idp.key})",
            value=idp.key,
        )
        for idp in idps
    ]
    try:
        selected: str | None = questionary.select(
            "Select an Identity Provider",
            choices=choices,
            style=_get_selection_style(),
        ).ask()
    except KeyboardInterrupt:
        sys.exit(0)

    if selected is None:
        sys.exit(0)
    return selected


def select_server(servers: list[Server]) -> Server:
    """Prompt the user to choose a Science Platform Server.

    Args:
        servers: Known servers scoped to the active Identity Provider.

    Returns:
        Selected server record.

    Raises:
        SystemExit: When the user cancels the prompt or no servers exist.
    """
    if not servers:
        sys.exit(1)

    if len(servers) == 1:
        return servers[0]

    choices = [
        questionary.Choice(
            title=f"{server.name or server.uri} ({server.uri})",
            value=server,
        )
        for server in servers
        if server.uri is not None
    ]
    if not choices:
        sys.exit(1)

    try:
        selected: Server | None = questionary.select(
            "Select a Science Platform Server",
            choices=choices,
            style=_get_selection_style(),
        ).ask()
    except KeyboardInterrupt:
        sys.exit(0)

    if selected is None:
        sys.exit(0)
    return selected
