"""Context command DTOs for machine output."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from canfar.models.dto.base import DtoBase

if TYPE_CHECKING:
    from canfar.models.dto.auth import AuthenticationDto
    from canfar.models.dto.server import ServerSummaryDto


class ContextPairDto(DtoBase):
    """Compatible Authentication and Server pair for ``context ls``."""

    authentication: AuthenticationDto = Field(
        description="Authentication record for the pair."
    )
    server: ServerSummaryDto | None = Field(
        default=None,
        description="Server summary when a compatible server exists.",
    )
    active: bool = Field(description="Whether this pair matches the active selection.")


class ContextShowDto(DtoBase):
    """Machine output payload for ``context show``."""

    authentication: AuthenticationDto | None = Field(
        default=None,
        description="Active authentication record when configured.",
    )
    server: ServerSummaryDto | None = Field(
        default=None,
        description="Active Server summary when selected.",
    )


class ContextListDto(DtoBase):
    """Machine output payload for ``context ls``."""

    pairs: list[ContextPairDto] = Field(
        default_factory=list,
        description="Compatible Authentication and Server pairs.",
    )
