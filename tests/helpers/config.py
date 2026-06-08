"""Test helpers for configuration fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import AnyUrl

from canfar.models.active import ActiveConfig
from canfar.models.config import Configuration
from canfar.models.config_compat import legacy_context_to_credential

if TYPE_CHECKING:
    from canfar.models.auth import OIDC, X509
    from canfar.models.http import Server


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
    servers: list[Server] = []
    active_server: AnyUrl | None = None

    if context.server is not None:
        server = context.server.model_copy(deep=True)
        updates: dict[str, object] = {"idp": idp}
        if server.uri is None:
            updates["uri"] = AnyUrl(f"ivo://test.{idp}/skaha")
        server = server.model_copy(update=updates)
        servers.append(server)
        active_server = server.uri

    return Configuration(
        active=ActiveConfig(authentication=idp, server=active_server),
        authentication=[credential],
        server=servers,
    )
