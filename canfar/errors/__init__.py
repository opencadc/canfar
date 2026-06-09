"""Structured error codes and machine-mode serialization for CANFAR."""

from canfar.errors.codes import ErrorCode
from canfar.errors.model import (
    StructuredError,
    structured_error_to_json,
    structured_error_to_yaml,
)

__all__ = [
    "ErrorCode",
    "StructuredError",
    "structured_error_to_json",
    "structured_error_to_yaml",
]
