"""Registry and discovery-related models for Canfar API.

This module contains Pydantic models related to server discovery and
server information.
"""

from __future__ import annotations

import os
from base64 import b64encode
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import (
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SecretStr,
)

DEFAULT_REGISTRY_HOST = "images.canfar.net"
"""Container Registry host used when a command or setting names none."""

ProbeStatus = Literal["pending", "connected", "timeout", "unreachable", "error"]
"""Discovery state of one Science Platform Server; every state but ``pending``
is an outcome."""


class IVOARegistry(BaseModel):
    """Model for registry contents."""

    name: str
    content: str
    source: str | None = None
    development: bool = False
    success: bool = True
    error: str | None = None


class Server(BaseModel):
    """Model to store Canfar Server endpoint information."""

    registry: str
    development: bool = False
    uri: str
    url: str
    status: int | None = None
    failure: Literal["timeout", "unreachable"] | None = None
    name: str | None = None


class ServerProbe(BaseModel):
    """Discovery state of one Science Platform Server.

    Discovery reports each Server as ``pending`` once the registries list it,
    then again with its outcome.

    Attributes:
        name: Server Name discovery gives the endpoint.
        uri: IVOA URI from the registry.
        url: Endpoint URL from the registry.
        status: ``pending`` while discovery checks the Server; ``connected``
            when its session capabilities were read; otherwise why discovery
            could not use it.
        detail: Short reason for a ``timeout``, ``unreachable``, or ``error``
            outcome.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    uri: str
    url: str
    status: ProbeStatus
    detail: str | None = None


def parse_host(value: Any) -> Any:
    """Reduce a Container Registry host or ``http(s)`` URL to ``host[:port]``.

    Args:
        value: Bare host, such as ``images.canfar.net``, or an ``http`` or
            ``https`` URL without a path, as a string or Pydantic URL.

    Returns:
        Lowercase ``host[:port]``. Other values are returned unchanged for
        Pydantic to reject.

    Raises:
        ValueError: If the value has another scheme, a path, or no host.
    """
    if isinstance(value, AnyUrl):
        value = str(value)
    if not isinstance(value, str):
        return value
    text = value.strip()
    parts = urlsplit(text if "://" in text else f"//{text}")
    if (
        parts.scheme not in {"", "http", "https"}
        or parts.path not in {"", "/"}
        or parts.query
        or parts.fragment
        or parts.username is not None
        or not parts.hostname
    ):
        msg = f"invalid container registry host {value!r}: expected HOST[:PORT]"
        raise ValueError(msg)
    return parts.netloc.lower()


RegistryHost = Annotated[str, BeforeValidator(parse_host)]
"""Container Registry ``host[:port]``, parsed from a bare host or URL."""

_Username = Annotated[
    str,
    Field(
        description="Username for the container registry.",
        min_length=1,
        max_length=255,
        examples=["shinybrar"],
    ),
]
_Secret = Annotated[
    SecretStr,
    Field(
        description="Secret for the container registry, such as a Harbor CLI secret.",
        min_length=1,
        max_length=255,
    ),
]


class RegistryCredential(BaseModel):
    """Saved credential for one Container Registry host."""

    model_config = ConfigDict(frozen=True)

    username: _Username
    secret: _Secret

    def header(self) -> str:
        """Return the ``X-Skaha-Registry-Auth`` value, base64 ``username:secret``.

        Returns:
            str: String encoded in base64 format.
        """
        pair = f"{self.username}:{self.secret.get_secret_value()}"
        return b64encode(pair.encode()).decode()


def _env_value(name: str) -> str:
    """Return an environment value, matching ``name`` without case."""
    folded = name.casefold()
    for key, value in os.environ.items():
        if key.casefold() == folded:
            return value.strip()
    return ""


def env_credential() -> RegistryCredential | None:
    """Return ``CANFAR_REGISTRY__USERNAME`` and ``CANFAR_REGISTRY__SECRET``.

    Both must be set. They are not tied to a host and are never written to
    the configuration file. Names match without case.

    Returns:
        The credential, or ``None`` when either value is missing.

    Raises:
        ValidationError: If a value is empty after stripping or longer than
            255 characters.
    """
    username = _env_value("CANFAR_REGISTRY__USERNAME")
    secret = _env_value("CANFAR_REGISTRY__SECRET")
    if not username or not secret:
        return None
    return RegistryCredential(username=username, secret=SecretStr(secret))
