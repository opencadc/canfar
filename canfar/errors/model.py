"""Structured error model for machine-readable CLI failures."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StructuredError(BaseModel):
    """Machine-readable error payload for CLI stderr in JSON or YAML modes.

    Attributes:
        code: Stable dotted-domain error code; ``ErrorCode`` members validate
            to their string values.
        message: Human-readable error summary.
        hint: Optional remediation guidance.
    """

    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="Stable dotted-domain error code.")
    message: str = Field(description="Human-readable error summary.")
    hint: str | None = Field(
        default=None,
        description="Optional remediation guidance.",
    )


class LoggingEnvironmentError(StructuredError):
    """Structured failure for an invalid CANFAR logging environment value."""

    env_var: str = Field(description="Invalid environment variable name.")
    provided_value: str = Field(description="Rejected environment value.")
    expected: list[str] = Field(description="Accepted logging-level values.")
