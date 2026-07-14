"""Structured error model and machine-mode serialization helpers."""

from __future__ import annotations

import json
from typing import Annotated

import yaml
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from canfar.errors.codes import ErrorCode


def _coerce_error_code(value: ErrorCode | str) -> str:
    """Normalize ErrorCode enum values to their dotted string form."""
    if isinstance(value, ErrorCode):
        return str(value.value)
    return value


_Code = Annotated[str, BeforeValidator(_coerce_error_code)]


class StructuredError(BaseModel):
    """Machine-readable error payload for CLI stderr in JSON or YAML modes.

    Attributes:
        code: Stable dotted-domain error code.
        message: Human-readable error summary.
        hint: Optional remediation guidance.
    """

    model_config = ConfigDict(extra="forbid")

    code: _Code = Field(description="Stable dotted-domain error code.")
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


def structured_error_to_json(error: StructuredError) -> str:
    """Serialize a structured error to a JSON string for machine-mode stderr.

    Args:
        error: Structured error to serialize.

    Returns:
        str: JSON document with code, message, and hint fields.
    """
    return json.dumps(error.model_dump(mode="json"), ensure_ascii=False)


def structured_error_to_yaml(error: StructuredError) -> str:
    """Serialize a structured error to a YAML string for machine-mode stderr.

    Args:
        error: Structured error to serialize.

    Returns:
        str: YAML document with code, message, and hint fields.
    """
    return yaml.safe_dump(
        error.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )
