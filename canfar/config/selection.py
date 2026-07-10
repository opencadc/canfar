"""Authentication and server selection helpers for configuration objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from canfar.models.config_compat import (
    AuthContext,
    LegacyContextsMapping,
    credential_to_legacy_context,
)

if TYPE_CHECKING:
    from pydantic import AnyUrl

    from canfar.models.auth import AuthenticationCredential
    from canfar.models.config import Configuration
    from canfar.models.http import Server


def get_credential(config: Configuration, idp: str) -> AuthenticationCredential:
    """Return the saved authentication credential for an IDP key."""
    try:
        return config.authentication[idp]
    except KeyError as exc:
        msg = f"Authentication record for IDP '{idp}' not found."
        raise KeyError(msg) from exc


def get_server_by_name(config: Configuration, name: str) -> Server:
    """Return a known server by Server Name."""
    try:
        return config.servers[name]
    except KeyError as exc:
        msg = f"Server '{name}' not found."
        raise KeyError(msg) from exc


def get_server_by_uri(config: Configuration, uri: str | AnyUrl) -> Server:
    """Return a known server by IVOA URI."""
    target = str(uri)
    for server in config.servers.values():
        if server.uri is not None and str(server.uri) == target:
            return server
    msg = f"Server '{target}' not found."
    raise KeyError(msg)


def get_active_server(config: Configuration) -> Server:
    """Return the active science platform server record."""
    if config.active.server is None:
        msg = "No active server selected."
        raise KeyError(msg)
    return get_server_by_name(config, config.active.server)


def get_server_for_idp(config: Configuration, idp: str) -> Server:
    """Return the best-known server for an IDP."""
    if config.active.authentication == idp and config.active.server is not None:
        return get_active_server(config)

    for server in config.servers.values():
        if server.idp == idp:
            return server
    msg = f"No server found for IDP '{idp}'."
    raise KeyError(msg)


def server_selection_history(config: Configuration) -> dict[str, str]:
    """Return remembered server selections seeded with the current active pair."""
    selections = dict(config.active.servers)
    if config.active.server is None:
        return selections
    try:
        server = get_active_server(config)
    except KeyError:
        return selections
    if server.idp == config.active.authentication and server.name is not None:
        selections[config.active.authentication] = server.name
    return selections


def get_remembered_server_for_idp(config: Configuration, idp: str) -> Server | None:
    """Return the last selected server for ``idp`` when still valid."""
    name = server_selection_history(config).get(idp)
    if name is None:
        return None
    try:
        server = get_server_by_name(config, name)
    except KeyError:
        return None
    if server.idp != idp:
        return None
    return server


def upsert_server(config: Configuration, server: Server) -> None:
    """Compatibility wrapper for Configuration-owned Server mutation."""
    config.upsert_server(server)


def set_active_selection(config: Configuration, idp: str, server: Server) -> None:
    """Compatibility wrapper for Configuration-owned Server Selection."""
    config.set_active_selection(idp, server)


def active_context(config: Configuration) -> AuthContext:
    """Return the active Authentication as a legacy ``AuthContext`` view."""
    credential = get_credential(config, config.active.authentication)
    try:
        server = get_active_server(config)
    except KeyError:
        server = None
    return credential_to_legacy_context(credential, server)


def legacy_contexts(config: Configuration) -> LegacyContextsMapping:
    """Return a legacy dict-like view keyed by IDP."""
    return LegacyContextsMapping(config)


def set_legacy_context(config: Configuration, idp: str, context: AuthContext) -> None:
    """Compatibility wrapper for Configuration-owned legacy context mutation."""
    config.set_legacy_context(idp, context)
