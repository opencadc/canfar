"""Active selection models for persisted configuration."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ActiveConfig(BaseModel):
    """Active authentication and server selection.

    Attributes:
        authentication: Canonical IDP key for the active authentication record.
        server: Server Name of the active science platform server.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    authentication: str = Field(
        description="Canonical IDP key for the active authentication record.",
    )
    server: str | None = Field(
        default=None,
        description=(
            "Server Name of the active science platform server, or ``None`` "
            "when no compatible server is selected."
        ),
    )
    servers: dict[str, str] = Field(
        default_factory=dict,
        description="Last selected science platform server name by IDP.",
    )
