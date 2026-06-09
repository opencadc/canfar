"""Authentication and server selection helpers for configuration objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from canfar.models.config_compat import (
    AuthContext,
    LegacyContextsMapping,
    credential_to_legacy_context,
    legacy_context_to_credential,
)

if TYPE_CHECKING:
    from pydantic import AnyUrl

    from canfar.models.auth import AuthenticationCredential
    from canfar.models.config import Configuration
    from canfar.models.http import Server


def get_credential(config: Configuration, idp: str) -> AuthenticationCredential:
    """Return the saved authentication credential for an IDP key."""
    for credential in config.authentication:
        if credential.idp == idp:
            return credential
    msg = f"Authentication record for IDP '{idp}' not found."
    raise KeyError(msg)


def get_server_by_uri(config: Configuration, uri: str | AnyUrl) -> Server:
    """Return a known server by IVOA URI."""
    target = str(uri)
    for server in config.server:
        if server.uri is not None and str(server.uri) == target:
            return server
    msg = f"Server '{target}' not found."
    raise KeyError(msg)


def get_active_server(config: Configuration) -> Server:
    """Return the active science platform server record."""
    if config.active.server is None:
        msg = "No active server selected."
        raise KeyError(msg)
    return get_server_by_uri(config, config.active.server)


def get_server_for_idp(config: Configuration, idp: str) -> Server:
    """Return the best-known server for an IDP."""
    if config.active.authentication == idp and config.active.server is not None:
        return get_active_server(config)

    for server in config.server:
        if server.idp == idp:
            return server
    msg = f"No server found for IDP '{idp}'."
    raise KeyError(msg)


def server_selection_history(config: Configuration) -> dict[str, AnyUrl]:
    """Return remembered server selections seeded with the current active pair."""
    selections = dict(config.active.servers)
    if config.active.server is None:
        return selections
    try:
        server = get_active_server(config)
    except KeyError:
        return selections
    if server.idp == config.active.authentication and server.uri is not None:
        selections[config.active.authentication] = server.uri
    return selections


def get_remembered_server_for_idp(config: Configuration, idp: str) -> Server | None:
    """Return the last selected server for ``idp`` when still valid."""
    uri = server_selection_history(config).get(idp)
    if uri is None:
        return None
    try:
        server = get_server_by_uri(config, uri)
    except KeyError:
        return None
    if server.idp != idp:
        return None
    return server


def upsert_server(config: Configuration, server: Server) -> None:
    """Insert or replace a server record keyed by URI."""
    if server.uri is None:
        return
    target = str(server.uri)
    updated: list[Server] = []
    replaced = False
    for existing in config.server:
        if existing.uri is not None and str(existing.uri) == target:
            updated.append(server)
            replaced = True
        else:
            updated.append(existing)
    if not replaced:
        updated.append(server)
    config.server = updated


def set_active_selection(config: Configuration, idp: str, server: Server) -> None:
    """Persist ``idp`` and ``server`` as the active Authentication/Server pair."""
    if server.uri is None:
        msg = "Server URI is required for active selection."
        raise ValueError(msg)

    uri = server.uri
    selected = server.model_copy(update={"idp": idp}, deep=True)
    upsert_server(config, selected)
    selections = server_selection_history(config)
    selections[idp] = uri
    config.active = config.active.model_copy(
        update={
            "authentication": idp,
            "server": uri,
            "servers": selections,
        },
    )


def with_active_selection(
    config: Configuration,
    idp: str,
    server: Server,
) -> Configuration:
    """Return a copy using ``idp`` and ``server`` as the active pair."""
    selected_config = config.model_copy(deep=True)
    set_active_selection(selected_config, idp, server)
    return selected_config


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
    """Update saved authentication and optional server from a legacy context."""
    credential = legacy_context_to_credential(context, idp)
    updated: list[AuthenticationCredential] = []
    replaced = False
    for existing in config.authentication:
        if existing.idp == idp:
            updated.append(credential)
            replaced = True
        else:
            updated.append(existing)
    if not replaced:
        updated.append(credential)
    config.authentication = updated

    if context.server is not None:
        upsert_server(config, context.server.model_copy(update={"idp": idp}))
