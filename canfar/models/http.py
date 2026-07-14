"""Client HTTP Models."""

from __future__ import annotations

from pydantic import AnyHttpUrl, AnyUrl, BaseModel, ConfigDict, Field

DEFAULT_SERVER_CORES = 2
"""Default CPU core limit when context enrichment is unavailable."""

DEFAULT_SERVER_RAM_GB = 16
"""Default RAM limit in GB when context enrichment is unavailable."""

DEFAULT_SERVER_GPUS = 0
"""Default GPU count when context enrichment is unavailable."""


class Server(BaseModel):
    """Science Platform Server Details."""

    model_config = ConfigDict(
        title="CANFAR Client Server Configuration",
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
        str_max_length=256,
        str_min_length=1,
    )

    name: str | None = Field(
        default=None,
        title="Server Name",
        description="Common name for the science platform server.",
        examples=["SRCnet-Sweden", "SRCnet-UK-CAM"],
        min_length=1,
        max_length=256,
        validate_default=False,
    )
    uri: AnyUrl | None = Field(
        default=None,
        title="Server URI identifier",
        description="IVOA static uri identifier for the server.",
        examples=["ivo://swesrc.chalmers.se/skaha", "ivo://canfar.cam.uksrc.org/skaha"],
    )
    url: AnyHttpUrl | None = Field(
        default=None,
        title="Server URL",
        description="URL where the server is currently accessible from.",
        examples=[
            "https://services.swesrc.chalmers.se/skaha",
            "https://canfar.cam.uksrc.org/skaha",
        ],
    )
    version: str | None = Field(
        default=None,
        title="API Version",
        description="Server API Version.",
        pattern=r"^v\d+(?:\.\d+)*$",
        examples=["v0", "v1", "v2"],
        min_length=2,
        max_length=8,
    )
    auths: list[str] | None = Field(
        default=None,
        title="Supported Auth Modes",
        description="Authentication modes supported by the Server",
        examples=["oidc", "token", "x509"],
    )
    idp: str | None = Field(
        default=None,
        title="Identity Provider Key",
        description="Canonical IDP key this server belongs to.",
        min_length=1,
        max_length=64,
    )
    cores: int = Field(
        default=DEFAULT_SERVER_CORES,
        title="Default CPU Core Limit",
        description="Default maximum CPU cores available for session creation.",
        ge=1,
    )
    ram: int = Field(
        default=DEFAULT_SERVER_RAM_GB,
        title="Default RAM Limit (GB)",
        description="Default maximum RAM in gigabytes for session creation.",
        ge=1,
    )
    gpus: int = Field(
        default=DEFAULT_SERVER_GPUS,
        title="Maximum GPU Count",
        description="Maximum GPUs available for session creation.",
        ge=0,
    )
    status: str | None = Field(
        default=None,
        title="Discovery Reachability Status",
        description=(
            "Persisted compatibility field for discovery reachability status "
            "when known."
        ),
    )
