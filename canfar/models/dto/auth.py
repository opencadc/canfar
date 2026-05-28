"""Authentication command DTOs for machine output."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from canfar.models.dto.base import DtoBase

AuthModeDto = Literal["x509", "oidc"]


class AuthenticationDto(DtoBase):
    """Machine output authentication record."""

    idp: str = Field(description="Canonical Identity Provider key.")
    name: str = Field(description="Human-readable IDP name.")
    mode: AuthModeDto = Field(description="Authentication mode.")
    expiry: float | None = Field(
        default=None,
        description="Credential expiry as Unix timestamp when applicable.",
    )
    active: bool = Field(description="Whether this record is active.")
    server: str | None = Field(
        default=None,
        description="Selected server URI reference when available.",
    )


class AuthenticationShowDto(DtoBase):
    """Machine output payload for ``auth show`` and default ``auth``."""

    authentication: AuthenticationDto = Field(
        description="Active authentication record.",
    )


class AuthenticationListDto(DtoBase):
    """Machine output payload for ``auth ls``."""

    authentications: list[AuthenticationDto] = Field(
        default_factory=list,
        description="Saved authentication records.",
    )
