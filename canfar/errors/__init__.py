"""Structured error codes and payloads for CANFAR."""

from canfar.errors.codes import ErrorCode
from canfar.errors.model import LoggingEnvironmentError, StructuredError

__all__ = [
    "ErrorCode",
    "LoggingEnvironmentError",
    "StructuredError",
]
