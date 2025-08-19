"""Registry and discovery-related models for Canfar API.

This module contains Pydantic models related to server discovery,
registry search configuration, and server information.
"""

from __future__ import annotations

from base64 import b64encode

from pydantic import AnyHttpUrl, BaseModel, Field, model_validator
from typing_extensions import Self


class IVOARegistrySearch(BaseModel):
    """Configuration model for server discovery settings."""

    registries: dict[str, str] = Field(
        default={
            "https://spsrc27.iaa.csic.es/reg/resource-caps": "SRCnet",
            "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps": "CADC",
            (
                "https://rc-ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
            ): "CADC@keel-dev",
        }
    )

    names: dict[str, str] = Field(
        default={
            "ivo://canfar.net/src/skaha": "Canada",
            "ivo://swesrc.chalmers.se/skaha": "Sweden",
            "ivo://canfar.cam.uksrc.org/skaha": "UK-CAM",
            "ivo://canfar.ral.uksrc.org/skaha": "UK-RAL",
            "ivo://src.skach.org/skaha": "Swiss",
            "ivo://espsrc.iaa.csic.es/skaha": "Spain",
            "ivo://canfar.itsrc.oact.inaf.it/skaha": "Italy",
            "ivo://shion-sp.mtk.nao.ac.jp/skaha": "Japan",
            "ivo://canfar.krsrc.kr/skaha": "Korea",
            "ivo://canfar.ska.zverse.space/skaha": "China",
            "ivo://cadc.nrc.ca/skaha": "CANFAR",
        }
    )

    omit: list[tuple[str, str]] = Field(
        default=[("CADC", "ivo://canfar.net/src/skaha")]
    )

    excluded: tuple[str, ...] = Field(
        default=("dev", "development", "test", "demo", "stage", "staging", "rc-")
    )


class IVOARegistry(BaseModel):
    """Model for registry contents."""

    name: str
    content: str
    success: bool = True
    error: str | None = None


class Server(BaseModel):
    """Model to store Canfar Server endpoint information."""

    registry: str
    uri: str
    url: str
    status: int | None = None
    name: str | None = None


class ServerResults(BaseModel):
    """Model for complete discovery results."""

    endpoints: list[Server] = Field(default_factory=list)
    total_time: float = 0.0
    registry_fetch_time: float = 0.0
    endpoint_check_time: float = 0.0
    found: int = 0
    checked: int = 0
    successful: int = 0

    def add(self, endpoint: Server) -> None:
        """Add an endpoint to results."""
        self.endpoints.append(endpoint)
        if endpoint.status == 200:
            self.successful += 1

    def get_by_registry(self) -> dict[str, list[Server]]:
        """Group endpoints by registry."""
        results: dict[str, list[Server]] = {}
        for endpoint in self.endpoints:
            if endpoint.registry not in results:
                results[endpoint.registry] = []
            results[endpoint.registry].append(endpoint)
        return results


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
