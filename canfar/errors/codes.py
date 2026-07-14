"""Phase-1 stable dotted error codes for CANFAR CLI and API contracts."""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    """Stable dotted-domain error codes for machine-mode automation.

    Values are contractual; message and hint text may evolve independently.
    """

    OUTPUT_CONFLICT = "output.conflict"
    OUTPUT_UNSUPPORTED_MODE = "output.unsupported_mode"
    AUTHENTICATION_REQUIRED = "authentication.required"
    AUTHENTICATION_CREDENTIAL_MISSING = "authentication.credential_missing"
    AUTHENTICATION_EXPIRED = "authentication.expired"
    AUTHENTICATION_CREDENTIAL_INVALID = "authentication.credential_invalid"
    SERVER_REQUIRED = "server.required"
    SERVER_DISCOVERY_FAILED = "server.discovery_failed"
    SERVER_NONE_AVAILABLE = "server.none_available"
    CONFIG_INVALID = "config.invalid"
    CONFIG_LOGIN_REQUIRED_AFTER_RESET = "config.login_required_after_reset"
    LOGGING_INVALID_ENV_VALUE = "logging.invalid_env_value"
    LOGGING_INVALID_FILE_PATH = "logging.invalid_file_path"
    LOGGING_FILE_SINK_UNAVAILABLE = "logging.file_sink_unavailable"
    TRANSPORT_FAILURE = "transport.failure"
    COMMAND_VALIDATION_FAILED = "command.validation_failed"
    COMMAND_CANCELLED = "command.cancelled"
