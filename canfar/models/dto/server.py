"""Server command DTOs for machine output."""

from __future__ import annotations

from pydantic import Field

from canfar.models.dto.base import DtoBase


class ServerSummaryDto(DtoBase):
    """Machine output summary for a science platform server.

    Attributes:
        name: Human-readable server name.
        idp: Canonical Identity Provider key.
        uri: IVOA server URI.
        url: HTTP base URL for the server.
        status: Discovery reachability status when known.
        version: Server API version.
        auths: Supported authentication modes.
        cores: Default CPU core limit when known.
        ram: Default RAM limit in GB when known.
        gpus: Maximum GPU count when known.
    """

    name: str | None = Field(default=None, description="Human-readable server name.")
    idp: str | None = Field(
        default=None,
        description="Canonical Identity Provider key.",
    )
    uri: str | None = Field(default=None, description="IVOA server URI.")
    url: str | None = Field(default=None, description="HTTP base URL.")
    status: str | None = Field(
        default=None,
        description="Discovery reachability status when known.",
    )
    version: str | None = Field(default=None, description="Server API version.")
    auths: list[str] | None = Field(
        default=None,
        description="Supported authentication modes.",
    )
    cores: int | None = Field(
        default=None,
        description="Default CPU core limit when known.",
    )
    ram: int | None = Field(
        default=None,
        description="Default RAM limit in GB when known.",
    )
    gpus: int | None = Field(
        default=None,
        description="Maximum GPU count when known.",
    )


class ServerListDto(DtoBase):
    """Machine output payload for ``server ls``."""

    servers: list[ServerSummaryDto] = Field(
        default_factory=list,
        description="Known server summaries for the active IDP.",
    )
