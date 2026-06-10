"""Test helpers for configuration fixtures."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import AnyUrl

from canfar.models.active import ActiveConfig
from canfar.models.config import Configuration
from canfar.models.config_compat import legacy_context_to_credential

if TYPE_CHECKING:
    from canfar.models.auth import OIDC, X509
    from canfar.models.http import Server


_SERVER_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def _server_config_key(name: str, fallback: str) -> str:
    if _SERVER_NAME_PATTERN.match(name):
        return name
    slug = re.sub(r"[^A-Za-z0-9_-]", "", name)
    if slug and _SERVER_NAME_PATTERN.match(slug):
        return slug
    return fallback


def servers_by_name(*servers: Server) -> dict[str, Server]:
    """Build a servers mapping from Server fixtures keyed by Server Name."""
    result: dict[str, Server] = {}
    for server in servers:
        if server.name is None:
            msg = "Server fixture must include a Server Name."
            raise ValueError(msg)
        result[server.name] = server
    return result


def assign_servers(config: Configuration, *servers: Server) -> None:
    """Replace saved servers and keep active Server Selection referentially valid."""
    config.servers = servers_by_name(*servers)
    if (
        config.active.server is not None
        and config.active.server not in config.servers
        and servers
        and servers[0].name is not None
    ):
        config.active = config.active.model_copy(update={"server": servers[0].name})


def configuration_from_legacy_context(key: str, context: OIDC | X509) -> Configuration:
    """Build a ``Configuration`` from a legacy auth context fixture.

    Args:
        key: Legacy context name used as the canonical IDP key (lowercased).
        context: Legacy authentication context with optional embedded server.

    Returns:
        Valid configuration instance mirroring the legacy fixture.
    """
    idp = key.lower()
    credential = legacy_context_to_credential(context, idp)
    servers: dict[str, Server] = {}
    active_server: str | None = None

    if context.server is not None:
        server = context.server.model_copy(deep=True)
        updates: dict[str, object] = {"idp": idp}
        if server.uri is None:
            updates["uri"] = AnyUrl(f"ivo://test.{idp}/skaha")
        if server.name is None:
            updates["name"] = idp
        server = server.model_copy(update=updates)
        key = _server_config_key(server.name or idp, idp)
        servers[key] = server.model_copy(update={"name": key}, deep=True)
        active_server = key

    return Configuration(
        active=ActiveConfig(authentication=idp, server=active_server),
        authentication={idp: credential},
        servers=servers,
    )
