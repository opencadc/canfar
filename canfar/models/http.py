"""Client HTTP Models."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import AnyHttpUrl, AnyUrl, BaseModel, ConfigDict, Field, field_validator

DEFAULT_SERVER_CORES = 2
"""Default CPU core limit when context enrichment is unavailable."""

DEFAULT_SERVER_RAM_GB = 16
"""Default RAM limit in GB when context enrichment is unavailable."""

DEFAULT_SERVER_GPUS = 0
"""Default GPU count when context enrichment is unavailable."""


class VOSpaceService(BaseModel):
    """VOSpace Service discovered through an IVOA registry."""

    model_config = ConfigDict(extra="forbid")

    uri: AnyUrl
    url: AnyHttpUrl

    @field_validator("url")
    @classmethod
    def _reject_capabilities_endpoint(cls, url: AnyHttpUrl) -> AnyHttpUrl:
        """Require the VOSpace base endpoint rather than its capabilities URL."""
        if (url.path or "").rstrip("/").endswith("/capabilities"):
            msg = "VOSpace Service base URL must not end with /capabilities."
            raise ValueError(msg)
        return url


class Server(BaseModel):
    """Science Platform Server Details."""

    model_config = ConfigDict(
        title="CANFAR Client Server Configuration",
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
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
    auths: list[Annotated[str, Field(max_length=256)]] | None = Field(
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
    storage: dict[str, VOSpaceService] = Field(
        default_factory=dict,
        title="VOSpace Services",
        description="VOSpace Services keyed by globally unique Storage Name.",
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
        max_length=256,
    )

    @field_validator("storage", mode="before")
    @classmethod
    def _validate_storage_names(cls, value: Any) -> Any:
        """Normalize and validate Storage Names before Pydantic transforms keys."""
        if not isinstance(value, dict):
            return value

        normalized: dict[str, Any] = {}
        original_name_by_normalized_name: dict[str, str] = {}
        for original_name, service in value.items():
            if not isinstance(original_name, str) or any(
                character in original_name for character in ":\x00\r\n"
            ):
                name = None
            else:
                name = original_name.strip()
            if name is None or (not name or name == "local" or name.startswith("-")):
                msg = (
                    f"Invalid Storage Name {original_name!r}: after whitespace "
                    "normalization it must be non-empty, differ from reserved 'local', "
                    "contain no colon, NUL, or newline, and not start with '-'."
                )
                raise ValueError(msg)
            if name in normalized:
                previous_original_name = original_name_by_normalized_name[name]
                msg = (
                    f"Storage Names {previous_original_name!r} and {original_name!r} "
                    f"both normalize to {name!r}; use unique names."
                )
                raise ValueError(msg)
            normalized[name] = service
            original_name_by_normalized_name[name] = original_name
        return normalized
