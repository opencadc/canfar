"""Session-related models for Canfar API.

This module contains Pydantic models related to session management,
including specifications for creating and fetching sessions.
"""

from __future__ import annotations

import contextlib
import warnings
from datetime import datetime
from typing import Annotated, Any, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from canfar.models.types import Kind, Status, View


class CreateRequest(BaseModel):
    """Payload specification for creating a new session."""

    name: str = Field(
        ...,
        description="A unique name for the session.",
        examples=["canfar-test"],
    )
    image: str = Field(
        ...,
        description="Container image to use for the session.",
        examples=["images.canfar.net/skaha/terminal:1.1.1"],
    )
    cores: int | None = Field(None, description="Number of cores.", ge=1, le=256)
    ram: int | None = Field(None, description="Amount of RAM (GB).", ge=1, le=512)
    kind: Kind = Field(
        ...,
        description="Type of canfar session.",
        examples=["headless", "notebook"],
        serialization_alias="type",
    )
    gpus: int | None = Field(None, description="Number of GPUs.", ge=1, le=28)
    cmd: str | None = Field(None, description="Command to run.", examples=["ls"])
    args: str | None = Field(
        None,
        description="Arguments to the command.",
        examples=["-la"],
    )
    env: dict[str, Any] | None = Field(
        None,
        description="Environment variables.",
        examples=[{"FOO": "BAR"}],
    )
    replicas: int = Field(
        1,
        description="Number of sessions to launch.",
        ge=1,
        le=512,
        exclude=True,
    )

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    # Validate that cmd, args and env are only used with headless sessions.
    @model_validator(mode="after")
    def _validate_headless(self) -> Self:
        """Validate that cmd, args and env are only used for headless sessions.

        Returns:
            Self: The validated model instance.
        """
        if (self.cmd or self.args or self.env) and self.kind != "headless":
            msg = "cmd, args, env only allowed for headless sessions."
            raise ValueError(msg)
        return self

    @field_validator("kind", mode="after")
    @classmethod
    def _validate_kind(cls, value: Kind, context: ValidationInfo) -> Kind:
        """Validate kind.

        Args:
            value (Kind): Value to validate.
            context (ValidationInfo): Class validation context.

        Returns:
            Kind: Validated value.
        """
        valid: tuple[str] = get_args(Kind)
        if value not in valid:
            msg = f"invalid session kind: {value}"
            raise ValueError(msg)

        if value in {"firefly", "desktop"} and (
            context.data.get("cmd")
            or context.data.get("args")
            or context.data.get("cores")
            or context.data.get("ram")
        ):
            warnings.warn(
                f"cmd, args, cores and ram ignored for {value} sessions.",
                stacklevel=2,
            )

        return value

    @field_validator("replicas")
    @classmethod
    def _validate_replicas(cls, value: int, context: ValidationInfo) -> int:
        """Validate replicas.

        Args:
            value (int): Value to validate.
            context (ValidationInfo): Class validation context.

        Returns:
            int: Validated value.
        """
        kind: str = context.data.get("kind", "")
        if kind in {"firefly", "desktop"} and value > 1:
            msg = f"multiple replicas invalid for {kind} sessions."
            raise ValueError(msg)
        return value

    @field_validator("image")
    @classmethod
    def _validate_image(cls, value: str) -> str:
        """Validate and normalize container image reference.

        Only supports the CANFAR registry (images.canfar.net).
        Adds default registry if not specified and :latest tag if no tag specified.

        Args:
            value (str): Container image reference.

        Returns:
            str: Normalized image reference.

        Raises:
            ValueError: If a custom registry is specified (not images.canfar.net).

        Examples:
            skaha/astroml -> images.canfar.net/skaha/astroml:latest
            skaha/astroml:v1.0 -> images.canfar.net/skaha/astroml:v1.0
            images.canfar.net/skaha/astroml -> images.canfar.net/skaha/astroml:latest
        """
        # Image Registry Format
        # registry.domain/repository/image:tag

        msg: str = "invalid image container reference."
        msg += "must follow the format [registry/]repository/image[:tag]"

        splits: list[str] = value.split("/")
        if len(splits) < 2 or len(splits) > 3:
            raise ValueError(msg)

        if len(splits) == 2:
            value = f"images.canfar.net/{value}"

        # Add :latest tag if no tag specified (check only the last component)
        if ":" not in value.split("/")[-1]:
            value += ":latest"

        return value


class FetchRequest(BaseModel):
    """Payload specification for fetching session[s] information."""

    kind: Kind | None = Field(
        None,
        description="Type of canfar session.",
        examples=["headless"],
        alias="type",
    )
    status: Status | None = Field(
        None,
        description="Status of the session.",
        examples=["Running"],
    )
    view: View | None = Field(None, description="Number of views.", examples=["all"])

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


# This model is excluded from pep8-naming checks, since its the data shape
# of the response from the server. See [tool.ruff.per-file-ignores] in pyproject.toml
class FetchResponse(BaseModel):
    """Data model for a single session returned by the fetch API."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(
        "Unknown",
        description="Unique identifier for the session.",
    )
    userid: str | None = Field(
        None,
        description="User identifier associated with the session.",
    )
    runAsUID: str | None = Field(
        None,
        description="UID the session runs under.",
    )
    runAsGID: str | None = Field(
        None,
        description="GID the session runs under.",
    )
    supplementalGroups: list[int] = Field(
        default_factory=list,
        description="Supplemental groups granted to the session.",
    )
    appid: str | None = Field(
        None,
        description="Optional application identifier.",
    )
    image: str | None = Field(
        None,
        description="Container image backing the session.",
    )
    type: Kind = Field(
        "headless",
        description="Session type as returned by the API.",
    )
    status: str = Field(
        "Unknown",
        description="Session status as returned by the API.",
    )
    name: str = Field(
        "Unknown",
        description="Session name supplied at creation time.",
    )
    startTime: datetime | None = Field(
        None,
        description="Timestamp when the session started.",
    )
    expiryTime: datetime | None = Field(
        None,
        description="Timestamp when the session will expire.",
    )
    connectURL: str | None = Field(
        None,
        description="URL to connect to the session.",
    )
    requestedRAM: str | None = Field(
        None,
        description="Requested RAM.",
    )
    requestedCPUCores: str | None = Field(
        None,
        description="Requested CPU cores.",
    )
    requestedGPUCores: str | None = Field(
        None,
        description="Requested GPU cores.",
    )
    ramInUse: str | None = Field(
        None,
        description="RAM in use.",
    )
    gpuRAMInUse: str | None = Field(
        None,
        description="GPU RAM in use.",
    )
    cpuCoresInUse: str | None = Field(
        None,
        description="CPU cores in use.",
    )
    gpuUtilization: str | None = Field(
        None,
        description="GPU utilization.",
    )
    isFixedResources: Annotated[
        bool,
        Field(
            description=(
                "Whether the session requests fixed resources (limits == requests). "
                "If False, the session is running in flexible mode."
            ),
        ),
    ] = True
    anomalies: list[str] = Field(default_factory=list, repr=False, exclude=True)

    @field_validator("type", mode="before")
    @classmethod
    def _validate_type(cls, v: Any) -> str:
        """Validate type field, fall back to 'headless' if invalid."""
        if v in (None, "", []):
            return "headless"
        if isinstance(v, str):
            # Check if it's a valid Kind value
            valid_kinds = get_args(Kind)
            if v in valid_kinds:
                return v
            # Invalid type, will be tracked as anomaly in model validator
            return "headless"
        return "headless"

    @field_validator("status", mode="before")
    @classmethod
    def _validate_status(cls, v: Any) -> str:
        """Validate status field, allow any string value."""
        if v in (None, "", []):
            return "Unknown"
        return str(v)

    @field_validator("supplementalGroups", mode="before")
    @classmethod
    def _validate_supplemental_groups(cls, v: Any) -> list[int]:
        """Coerce supplemental groups to list of integers."""
        if not isinstance(v, list):
            return []
        result = []
        for item in v:
            with contextlib.suppress(ValueError, TypeError):
                result.append(int(item))
        return result

    @field_validator("startTime", "expiryTime", mode="before")
    @classmethod
    def _validate_datetime(cls, v: Any) -> datetime | None:
        """Parse datetime fields, return None if invalid."""
        if v in (None, "", []):
            return None
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            try:
                iso_time = v.replace("Z", "+00:00")
                return datetime.fromisoformat(iso_time)
            except (TypeError, ValueError):
                return None
        return None

    @field_validator("id", "name", mode="before")
    @classmethod
    def _validate_string_fields(cls, v: Any) -> str:
        """Validate string fields, default to 'Unknown' if missing."""
        if v in (None, "", []):
            return "Unknown"
        return str(v)

    @model_validator(mode="after")
    def _collect_anomalies(self) -> Self:
        """Collect anomalies for missing or invalid fields."""
        notes: list[str] = []

        # Track missing/invalid fields
        if self.id == "Unknown":
            notes.append("missing id in response")
        if self.name == "Unknown":
            notes.append("missing name in response")
        if self.type == "headless":
            # Only track as anomaly if it was actually missing/invalid
            # We can't easily tell here, so we'll skip this
            pass
        if self.startTime is None:
            notes.append("missing or invalid startTime in response")
        if self.expiryTime is None:
            notes.append("missing or invalid expiryTime in response")

        # Track missing resource fields
        for attr in ["ramInUse", "cpuCoresInUse"]:
            value = getattr(self, attr)
            if value in (None, "", []):
                notes.append(f"missing or invalid {attr} in response")

        if notes:
            self.anomalies = self.anomalies + notes
        return self
