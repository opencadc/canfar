"""Tests for CLI machine output infrastructure."""

from __future__ import annotations

import json
from io import StringIO

import pytest
import yaml

from canfar.cli.output import (
    OUTPUT_CONFLICT_EXIT_CODE,
    OutputConflictError,
    OutputMode,
    StructuredError,
    parse_leaf_output_flags,
    parse_output_flags,
    parse_top_level_output_flags,
    render_stderr_error,
    render_stdout,
    write_stderr_error,
    write_stdout,
)
from canfar.models.dto.base import DtoBase, dto_dump


class SampleDto(DtoBase):
    """Sample DTO for serialization tests."""

    name: str
    optional: str | None = None


def test_output_mode_values() -> None:
    """OutputMode exposes human, json, and yaml members."""
    assert OutputMode.HUMAN.value == "human"
    assert OutputMode.JSON.value == "json"
    assert OutputMode.YAML.value == "yaml"


def test_parse_top_level_output_flags_before_command_path() -> None:
    """Top-level flags before the command path select machine output mode."""
    assert parse_top_level_output_flags(["--json", "auth", "ls"]) == OutputMode.JSON
    assert parse_top_level_output_flags(["--yaml", "ps"]) == OutputMode.YAML
    assert parse_top_level_output_flags(["auth", "ls"]) is None


def test_parse_leaf_output_flags_after_command_path() -> None:
    """Leaf flags after the command path select machine output mode."""
    assert parse_leaf_output_flags(["auth", "ls", "--json"]) == OutputMode.JSON
    assert parse_leaf_output_flags(["ps", "--yaml"]) == OutputMode.YAML
    assert parse_leaf_output_flags(["auth", "ls"]) is None


def test_parse_output_flags_ignores_middle_group_placement() -> None:
    """Intermediate group placement is not a supported output flag location."""
    assert parse_output_flags(["auth", "--json", "ls"]) == OutputMode.HUMAN


def test_parse_output_flags_defaults_to_human() -> None:
    """No machine flags resolves to human output mode."""
    assert parse_output_flags(["auth", "ls"]) == OutputMode.HUMAN


def test_parse_output_flags_top_level_only() -> None:
    """Top-level placement alone selects machine output mode."""
    assert parse_output_flags(["--json", "auth", "ls"]) == OutputMode.JSON


def test_parse_output_flags_leaf_only() -> None:
    """Leaf placement alone selects machine output mode."""
    assert parse_output_flags(["auth", "ls", "--yaml"]) == OutputMode.YAML


def test_parse_output_flags_same_mode_at_both_placements_is_idempotent() -> None:
    """Duplicate same-mode flags across placements remain idempotent."""
    assert parse_output_flags(["--json", "ps", "--json"]) == OutputMode.JSON
    assert parse_output_flags(["--yaml", "auth", "ls", "--yaml"]) == OutputMode.YAML


def test_parse_output_flags_duplicate_same_mode_at_top_level_is_idempotent() -> None:
    """Duplicate same-mode flags at one placement remain idempotent."""
    assert parse_output_flags(["--json", "--json", "auth", "ls"]) == OutputMode.JSON


def test_parse_output_flags_conflicting_modes_exit_two() -> None:
    """Different machine modes across placements raise output.conflict."""
    with pytest.raises(OutputConflictError) as exc_info:
        parse_output_flags(["--json", "ps", "--yaml"])

    assert exc_info.value.code == "output.conflict"
    assert exc_info.value.exit_code == OUTPUT_CONFLICT_EXIT_CODE


def test_parse_output_flags_conflicting_modes_at_top_level() -> None:
    """Different machine modes at the same placement raise output.conflict."""
    with pytest.raises(OutputConflictError) as exc_info:
        parse_output_flags(["--json", "--yaml", "auth", "ls"])

    assert exc_info.value.code == "output.conflict"
    assert exc_info.value.exit_code == OUTPUT_CONFLICT_EXIT_CODE


def test_dto_dump_includes_null_fields() -> None:
    """DTO serialization keeps declared null fields for stable machine keys."""
    payload = dto_dump(SampleDto(name="cadc"))
    assert payload == {"name": "cadc", "optional": None}


def test_render_stdout_json_is_data_only() -> None:
    """JSON stdout rendering emits serialized data without diagnostics."""
    rendered = render_stdout({"idp": "cadc"}, OutputMode.JSON)
    assert json.loads(rendered) == {"idp": "cadc"}


def test_render_stdout_yaml_is_data_only() -> None:
    """YAML stdout rendering emits serialized data without diagnostics."""
    rendered = render_stdout({"idp": "cadc"}, OutputMode.YAML)
    assert yaml.safe_load(rendered) == {"idp": "cadc"}


def test_render_stdout_human_is_empty() -> None:
    """Human mode does not emit machine payloads on stdout."""
    assert render_stdout({"idp": "cadc"}, OutputMode.HUMAN) == ""


def test_render_stderr_error_json_on_stderr_channel() -> None:
    """JSON machine errors render structured payloads for stderr."""
    error = StructuredError(
        code="output.conflict",
        message="Conflicting output flags.",
        hint="Use only one of --json or --yaml.",
    )
    rendered = render_stderr_error(error, OutputMode.JSON)
    payload = json.loads(rendered)
    assert payload["code"] == "output.conflict"
    assert payload["message"] == "Conflicting output flags."
    assert payload["hint"] == "Use only one of --json or --yaml."


def test_render_stderr_error_yaml_on_stderr_channel() -> None:
    """YAML machine errors render structured payloads for stderr."""
    error = StructuredError(
        code="server.required",
        message="No active server selected.",
        hint="Run canfar server use.",
    )
    rendered = render_stderr_error(error, OutputMode.YAML)
    payload = yaml.safe_load(rendered)
    assert payload["code"] == "server.required"
    assert payload["message"] == "No active server selected."
    assert payload["hint"] == "Run canfar server use."


def test_write_stdout_and_stderr_separation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stdout and stderr writers keep machine data and errors separate."""
    stdout = StringIO()
    stderr = StringIO()
    monkeypatch.setattr("sys.stdout", stdout)
    monkeypatch.setattr("sys.stderr", stderr)

    write_stdout({"sessions": []}, OutputMode.JSON)
    write_stderr_error(
        StructuredError(
            code="transport.failure",
            message="Request failed.",
        ),
        OutputMode.JSON,
    )

    assert json.loads(stdout.getvalue()) == {"sessions": []}
    assert json.loads(stderr.getvalue())["code"] == "transport.failure"
    assert stdout.getvalue().strip() != stderr.getvalue().strip()


def test_render_stdout_accepts_pydantic_dto() -> None:
    """Stdout rendering accepts DTO models via shared dump helpers."""
    rendered = render_stdout(SampleDto(name="srcnet", optional=None), OutputMode.JSON)
    assert json.loads(rendered) == {"name": "srcnet", "optional": None}
