"""Test helpers for configuration fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import AnyHttpUrl, AnyUrl

from canfar.models.active import ActiveConfig
from canfar.models.auth import (
    Client,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
    X509Credential,
)
from canfar.models.config import Configuration
from canfar.models.http import Server

if TYPE_CHECKING:
    from pathlib import Path

    from canfar.models.auth import AuthenticationCredential


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


def oidc_credential(
    idp: str = "test",
    *,
    discovery: str | None = "https://oidc.example.com/.well-known/openid-configuration",
    token_url: str = "https://oidc.example.com/token",  # noqa: S107
    identity: str = "test-client",
    secret: str = "test-secret",  # noqa: S107
    access: str = "access-token",
    refresh: str = "refresh-token",
    access_expiry: float = 9_999_999_999.0,
    refresh_expiry: float = 9_999_999_999.0,
) -> OIDCCredential:
    """Build a complete OIDC credential for tests."""
    return OIDCCredential(
        idp=idp,
        endpoints=Endpoint(discovery=discovery, token=token_url),
        client=Client(identity=identity, secret=secret),
        token=Token(access=access, refresh=refresh),
        expiry=Expiry(access=access_expiry, refresh=refresh_expiry),
    )


def x509_credential(
    idp: str = "test",
    *,
    path: Path | None = None,
    expiry: float = 9_999_999_999.0,
) -> X509Credential:
    """Build an X.509 credential for tests."""
    return X509Credential(idp=idp, path=path, expiry=expiry)


def configuration_with_credential(
    credential: AuthenticationCredential,
    *,
    server: Server | None = None,
) -> Configuration:
    """Build a ``Configuration`` with one credential and optional server.

    Args:
        credential: Authentication credential to store.
        server: Optional server to include. Server ``idp`` is set to match credential.

    Returns:
        Valid configuration instance.
    """
    idp = credential.idp
    servers: dict[str, Server] = {}
    active_server: str | None = None

    if server is not None:
        s = server.model_copy(update={"idp": idp}, deep=True)
        if s.name is None:
            s = s.model_copy(update={"name": idp})
        if s.uri is None:
            s = s.model_copy(update={"uri": AnyUrl(f"ivo://test.{idp}/skaha")})
        assert s.name is not None
        servers[s.name] = s
        active_server = s.name

    return Configuration(
        active=ActiveConfig(authentication=idp, server=active_server),
        authentication={idp: credential},
        servers=servers,
    )


def oidc_config(
    idp: str = "test",
    *,
    server_name: str = "TestOIDC",
    server_url: str = "https://oidc.example.com",
    access_expiry: float = 9_999_999_999.0,
    refresh_expiry: float = 9_999_999_999.0,
    **kwargs: object,
) -> Configuration:
    """Build a Configuration with an OIDC credential and server."""
    cred = oidc_credential(
        idp,
        access_expiry=access_expiry,
        refresh_expiry=refresh_expiry,
        **kwargs,
    )
    server = Server(name=server_name, url=AnyHttpUrl(server_url), version="v1")
    return configuration_with_credential(cred, server=server)


def x509_config(
    idp: str = "test",
    *,
    server_name: str = "TestX509",
    server_url: str = "https://x509.example.com",
    path: Path | None = None,
    expiry: float = 9_999_999_999.0,
    version: str = "v1",
) -> Configuration:
    """Build a Configuration with an X.509 credential and server."""
    cred = x509_credential(idp, path=path, expiry=expiry)
    server = Server(name=server_name, url=AnyHttpUrl(server_url), version=version)
    return configuration_with_credential(cred, server=server)
