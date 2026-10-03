"""Client HTTP Models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Any

from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    ValidationError,
    field_validator,
    model_validator,
)
from typing_extensions import Self

LOCAL = "local"
"""Reserved Storage Identifier for the machine where the code runs."""


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


class ResourceRange(BaseModel):
    """Inclusive range of whole-number Session resource values."""

    model_config = ConfigDict(extra="forbid")

    min: int = Field(title="Minimum", description="Smallest value.", ge=0)
    max: int = Field(title="Maximum", description="Largest value.", ge=0)

    @model_validator(mode="after")
    def _check_order(self) -> Self:
        """Reject a range whose minimum exceeds its maximum."""
        if self.min > self.max:
            msg = f"Minimum {self.min} exceeds maximum {self.max}."
            raise ValueError(msg)
        return self

    def __str__(self) -> str:
        """Return ``min-max``, or one value when both bounds match."""
        return str(self.min) if self.min == self.max else f"{self.min}-{self.max}"


class SessionResources(BaseModel):
    """CPU and memory bounds for one Resource Allocation Mode."""

    model_config = ConfigDict(extra="forbid")

    cores: ResourceRange | None = Field(
        default=None,
        title="CPU Cores",
        description="CPU core bounds; None when the Server does not advertise them.",
    )
    ram: ResourceRange | None = Field(
        default=None,
        title="RAM (GB)",
        description=(
            "Memory bounds in GB; None when the Server does not advertise them."
        ),
    )


class ServerResources(BaseModel):
    """Session resource limits advertised by a Science Platform Server.

    ``None`` marks a value the Server does not advertise.
    """

    model_config = ConfigDict(extra="forbid")

    flexible: SessionResources = Field(
        default_factory=SessionResources,
        title="Flexible Resources",
        description=(
            "Sessions without explicit CPU or memory: the guaranteed request (min) "
            "and the burst limit (max)."
        ),
    )
    fixed: SessionResources = Field(
        default_factory=SessionResources,
        title="Fixed Resources",
        description=(
            "Sessions with explicit CPU or memory: the smallest (min) and largest "
            "(max) values the Server accepts."
        ),
    )
    gpus: ResourceRange | None = Field(
        default=None,
        title="GPUs",
        description="GPU counts a Session can request; 0 to 0 when none are offered.",
    )
    sessions: int | None = Field(
        default=None,
        title="Interactive Session Limit",
        description=(
            "Maximum Pending or Running interactive Sessions per user; headless "
            "Sessions do not count."
        ),
        ge=1,
    )

    @classmethod
    def from_context(cls, payload: Mapping[str, Any]) -> Self:
        """Read limits from a Science Platform Server context payload.

        Values the payload omits or malforms stay ``None``, so older platform
        versions produce partial resources.

        Args:
            payload: JSON object from the Server's context endpoint, as returned
                by ``canfar.context.Context().resources()``.

        Returns:
            Limits for each Resource Allocation Mode, GPUs, and Sessions.

        Raises:
            ValueError: If the payload advertises no recognizable limit.

        Examples:
            >>> from canfar.models.http import ServerResources
            >>> ServerResources.from_context(
            ...     {
            ...         "cores": {
            ...             "defaultRequest": 1,
            ...             "defaultLimit": 2,
            ...             "options": [1, 2, 4],
            ...         },
            ...         "gpus": {"options": []},
            ...     }
            ... ).fixed.cores
            ResourceRange(min=1, max=4)
        """
        cores = _section(payload, "cores")
        memory = _section(payload, "memoryGB")
        resources = cls(
            flexible=SessionResources(
                cores=_bounds(cores.get("defaultRequest"), cores.get("defaultLimit")),
                ram=_bounds(memory.get("defaultRequest"), memory.get("defaultLimit")),
            ),
            fixed=SessionResources(
                cores=_span(cores.get("options")),
                ram=_span(memory.get("options")),
            ),
            gpus=_span(
                _section(payload, "gpus").get("options"),
                empty=ResourceRange(min=0, max=0),
            ),
            sessions=_sessions(payload.get("maxInteractiveSessions")),
        )
        if resources == cls():
            msg = "Context payload advertises no recognizable resource limits."
            raise ValueError(msg)
        return resources


_OPTIONS = TypeAdapter(list[int])
_SESSIONS = TypeAdapter(Annotated[int, Field(ge=1)])


def _section(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    """Return one resource section of a context payload, or an empty mapping."""
    section = payload.get(key)
    return section if isinstance(section, Mapping) else {}


def _bounds(low: object, high: object) -> ResourceRange | None:
    """Return an inclusive range, or None when a bound is missing or invalid."""
    try:
        return ResourceRange.model_validate({"min": low, "max": high})
    except ValidationError:
        return None


def _span(
    options: object,
    *,
    empty: ResourceRange | None = None,
) -> ResourceRange | None:
    """Return the smallest-to-largest range of advertised options."""
    try:
        values = _OPTIONS.validate_python(options)
    except ValidationError:
        return None
    if not values:
        return empty
    return _bounds(min(values), max(values))


def _sessions(value: object) -> int | None:
    """Return a positive Session count, or None when missing or invalid."""
    try:
        return _SESSIONS.validate_python(value)
    except ValidationError:
        return None


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
        description="VOSpace Services keyed by globally unique Storage Identifier.",
    )
    resources: ServerResources | None = Field(
        default=None,
        title="Session Resources",
        description=(
            "Session resource limits read from the Server's context endpoint; "
            "None when unknown."
        ),
    )

    @field_validator("storage", mode="before")
    @classmethod
    def _validate_storage_identifiers(cls, value: Any) -> Any:
        """Normalize and validate Storage Identifiers before key transforms."""
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
            if name is None or (not name or name == LOCAL or name.startswith("-")):
                msg = (
                    f"Invalid Storage Identifier {original_name!r}: after whitespace "
                    "normalization it must be non-empty, differ from reserved "
                    f"'{LOCAL}', contain no colon, NUL, or newline, and not start "
                    "with '-'."
                )
                raise ValueError(msg)
            if name in normalized:
                previous_original_name = original_name_by_normalized_name[name]
                msg = (
                    f"Storage Identifiers {previous_original_name!r} and "
                    f"{original_name!r} "
                    f"both normalize to {name!r}; use unique names."
                )
                raise ValueError(msg)
            normalized[name] = service
            original_name_by_normalized_name[name] = original_name
        return normalized
