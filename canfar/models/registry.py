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
            "https://spsrc27.iaa.csic.es/reg/resource-caps": "SRCNet",
            "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps": "CADC",
            (
                "https://rc-ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
            ): "CADC@keel-dev",
        }
    )

    preferred_storage_leaf: str | None = None

    names: dict[str, str] = Field(
        default={
            "ivo://canfar.net/src/skaha": "canSRC",
            "ivo://swesrc.chalmers.se/skaha": "sweSRC",
            "ivo://canfar.cam.uksrc.org/skaha": "ukCAM",
            "ivo://canfar.ral.uksrc.org/skaha": "ukRAL",
            "ivo://src.skach.org/skaha": "chSRC",
            "ivo://espsrc.iaa.csic.es/skaha": "espSRC",
            "ivo://canfar.itsrc.oact.inaf.it/skaha": "itaINAF",
            "ivo://shion-sp.mtk.nao.ac.jp/skaha": "jpSRC",
            "ivo://canfar.krsrc.kr/skaha": "krSRC",
            "ivo://canfar.ska.zverse.space/skaha": "cnSRC",
            "ivo://canfar.itsrc.ext.cineca.it/skaha": "itCINECA",
            "ivo://canfar.srcnet.skao.int/skaha": "skaSRC",
            "ivo://aussrc.org/skaha": "ausSRC",
            "ivo://cadc.nrc.ca/skaha": "canfar",
        }
    )

    omit: list[tuple[str, str]] = Field(
        default=[("CADC", "ivo://canfar.net/src/skaha")]
    )

    excluded: tuple[str, ...] = Field(
        default=(
            "dev",
            "development",
            "test",
            "demo",
            "stage",
            "staging",
            "rc-",
            "preprod",
        )
    )


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
    name: str | None = None


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
