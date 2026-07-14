"""Tests for structured error codes and machine-mode serialization."""

from __future__ import annotations

import json

import yaml

from canfar.errors import (
    ErrorCode,
    StructuredError,
    structured_error_to_json,
    structured_error_to_yaml,
)


class TestErrorCode:
    """Tests for Phase-1 stable dotted error codes."""

    def test_phase1_error_codes(self) -> None:
        """Phase-1 codes use stable dotted-domain strings."""
        expected = {
            "OUTPUT_CONFLICT": "output.conflict",
            "OUTPUT_UNSUPPORTED_MODE": "output.unsupported_mode",
            "AUTHENTICATION_REQUIRED": "authentication.required",
            "AUTHENTICATION_CREDENTIAL_MISSING": "authentication.credential_missing",
            "AUTHENTICATION_EXPIRED": "authentication.expired",
            "AUTHENTICATION_CREDENTIAL_INVALID": "authentication.credential_invalid",
            "SERVER_REQUIRED": "server.required",
            "SERVER_DISCOVERY_FAILED": "server.discovery_failed",
            "SERVER_NONE_AVAILABLE": "server.none_available",
            "CONFIG_INVALID": "config.invalid",
            "CONFIG_LOGIN_REQUIRED_AFTER_RESET": "config.login_required_after_reset",
            "LOGGING_INVALID_ENV_VALUE": "logging.invalid_env_value",
            "LOGGING_INVALID_FILE_PATH": "logging.invalid_file_path",
            "LOGGING_FILE_SINK_UNAVAILABLE": "logging.file_sink_unavailable",
            "TRANSPORT_FAILURE": "transport.failure",
            "COMMAND_VALIDATION_FAILED": "command.validation_failed",
            "COMMAND_CANCELLED": "command.cancelled",
        }
        for name, value in expected.items():
            assert getattr(ErrorCode, name).value == value


class TestStructuredError:
    """Tests for the StructuredError model."""

    def test_fields(self) -> None:
        """StructuredError exposes code, message, and optional hint."""
        error = StructuredError(
            code=ErrorCode.SERVER_REQUIRED,
            message="No active server selected.",
            hint="Run `canfar server use <name-or-uri>`.",
        )
        assert error.code == "server.required"
        assert error.message == "No active server selected."
        assert error.hint == "Run `canfar server use <name-or-uri>`."

    def test_hint_defaults_to_none(self) -> None:
        """Hint is optional and defaults to None."""
        error = StructuredError(
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            message="Authentication is required.",
        )
        assert error.hint is None


class TestStructuredErrorSerialization:
    """Tests for JSON and YAML machine-mode stderr serialization."""

    def test_structured_error_to_json(self) -> None:
        """JSON serialization includes code, message, and hint."""
        error = StructuredError(
            code=ErrorCode.OUTPUT_CONFLICT,
            message="Conflicting machine output flags.",
            hint="Use only one of --json or --yaml.",
        )
        payload = json.loads(structured_error_to_json(error))
        assert payload == {
            "code": "output.conflict",
            "message": "Conflicting machine output flags.",
            "hint": "Use only one of --json or --yaml.",
        }

    def test_structured_error_to_json_includes_null_hint(self) -> None:
        """JSON serialization keeps declared null hint fields."""
        error = StructuredError(
            code=ErrorCode.TRANSPORT_FAILURE,
            message="Request failed.",
        )
        payload = json.loads(structured_error_to_json(error))
        assert payload == {
            "code": "transport.failure",
            "message": "Request failed.",
            "hint": None,
        }

    def test_structured_error_to_yaml(self) -> None:
        """YAML serialization includes code, message, and hint."""
        error = StructuredError(
            code=ErrorCode.CONFIG_INVALID,
            message="Config file is invalid.",
            hint="Check ~/.canfar/config.yaml.",
        )
        payload = yaml.safe_load(structured_error_to_yaml(error))
        assert payload == {
            "code": "config.invalid",
            "message": "Config file is invalid.",
            "hint": "Check ~/.canfar/config.yaml.",
        }

    def test_structured_error_to_yaml_includes_null_hint(self) -> None:
        """YAML serialization keeps declared null hint fields."""
        error = StructuredError(
            code=ErrorCode.COMMAND_VALIDATION_FAILED,
            message="Command payload failed validation.",
        )
        payload = yaml.safe_load(structured_error_to_yaml(error))
        assert payload == {
            "code": "command.validation_failed",
            "message": "Command payload failed validation.",
            "hint": None,
        }
