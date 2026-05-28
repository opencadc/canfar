"""Platform routing context helpers for CLI and API workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from canfar.authentication import Authentication, AuthenticationError
from canfar.authentication import (
    list as auth_list,
)
from canfar.authentication import (
    show as auth_show,
)
from canfar.models.config import Configuration

if TYPE_CHECKING:
    from canfar.models.http import Server


def show() -> tuple[Authentication | None, Server | None]:
    """Return active authentication and server records.

    Returns:
        Active authentication record and active server. Either may be ``None``.
    """
    config = Configuration()
    try:
        authentication = auth_show()
    except AuthenticationError:
        authentication = None

    server: Server | None = None
    if config.active.server is not None:
        try:
            server = config.get_active_server()
        except KeyError:
            server = None
    return authentication, server


def list_pairs() -> list[tuple[Authentication, Server | None, bool]]:
    """Return compatible authentication and server pairs.

    Returns:
        Saved authentication records paired with a compatible server when one
        exists. Order not guaranteed.
    """
    config = Configuration()
    records = auth_list()
    pairs: list[tuple[Authentication, Server | None, bool]] = []

    for record in records:
        compatible = _compatible_server(config, record.idp)
        active = (
            record.active
            and config.active.server is not None
            and compatible is not None
            and compatible.uri is not None
            and str(compatible.uri) == str(config.active.server)
        )
        pairs.append((record, compatible, active))

    return pairs


def _compatible_server(config: Configuration, idp: str) -> Server | None:
    """Return the best known server for ``idp`` when one exists."""
    servers = [server for server in config.server if server.idp == idp]
    if not servers:
        return None

    if config.active.server is not None:
        for server in servers:
            if server.uri is not None and str(server.uri) == str(config.active.server):
                return server

    if len(servers) == 1:
        return servers[0]

    if config.active.authentication == idp and config.active.server is not None:
        try:
            return config.get_active_server()
        except KeyError:
            return servers[0]

    return servers[0]
