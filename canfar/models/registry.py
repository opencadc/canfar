"""Registry and discovery-related models for Canfar API.

This module contains Pydantic models related to server discovery and
server information.
"""

from __future__ import annotations

from base64 import b64encode
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator
from typing_extensions import Self

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


class ContainerRegistry(BaseModel):
    """Authentication details for private container registry."""

    url: AnyHttpUrl | None = Field(default=None, description="Container Registry URL")
    username: str | None = Field(
        default=None,
        description="Username for the container registry",
        min_length=1,
        max_length=255,
        examples=["shinybrar"],
    )
    secret: str | None = Field(
        default=None,
        description="Secret for the container registry",
        min_length=1,
        max_length=255,
        examples=["sup3rs3cr3t"],
    )

    @model_validator(mode="after")
    def _check_container_registry(self) -> Self:
        """Check if the container registry is configured correctly.

        Raises:
            ValueError: If the secret is provided without a username.
            ValueError: If the username is provided without a secret.

        Returns:
            Self: The validated model instance.
        """
        if self.username and not self.secret:
            msg = "container registry secret is required."
            raise ValueError(msg)
        if self.secret and not self.username:
            msg = "container registry username is required."
            raise ValueError(msg)
        return self

    def encoded(self) -> str:
        """Return the encoded username:secret.

        Returns:
            str: String encoded in base64 format.
        """
        return b64encode(f"{self.username}:{self.secret}".encode()).decode()
