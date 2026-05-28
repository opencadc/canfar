"""Active selection models for config v1."""

from __future__ import annotations

from pydantic import AnyUrl, BaseModel, ConfigDict, Field


class ActiveConfig(BaseModel):
    """Active authentication and server selection for config v1.

    Attributes:
        authentication: Canonical IDP key for the active authentication record.
        server: IVOA URI of the active science platform server.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    authentication: str = Field(
        description="Canonical IDP key for the active authentication record.",
    )
    server: AnyUrl | None = Field(
        default=None,
        description=(
            "IVOA URI of the active science platform server, or ``None`` "
            "when no compatible server is selected."
        ),
    )
