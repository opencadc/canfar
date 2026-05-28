"""Tests for CLI machine output infrastructure."""

from __future__ import annotations

import json
from io import StringIO

import pytest
import yaml

from canfar.cli import output
from canfar.errors import StructuredError
from canfar.models.dto.base import DtoBase, dto_dump


class SampleDto(DtoBase):
    """Sample DTO for serialization tests."""

    name: str
    optional: str | None = None


def test_output_mode_values() -> None:
    """OutputMode exposes human, json, and yaml members."""
    assert output.OutputMode.HUMAN.value == "human"
    assert output.OutputMode.JSON.value == "json"
    assert output.OutputMode.YAML.value == "yaml"


def test_parse_top_level_output_flags_before_command_path() -> None:
    """Top-level flags before the command path select machine output mode."""
    assert output.parse_prefix(["--json", "auth", "ls"]) == output.OutputMode.JSON
    assert output.parse_prefix(["--yaml", "ps"]) == output.OutputMode.YAML
    assert output.parse_prefix(["auth", "ls"]) is None


def test_parse_leaf_output_flags_after_command_path() -> None:
    """Leaf flags after the command path select machine output mode."""
    assert output.parse_suffix(["auth", "ls", "--json"]) == output.OutputMode.JSON
    assert output.parse_suffix(["ps", "--yaml"]) == output.OutputMode.YAML
    assert output.parse_suffix(["auth", "ls"]) is None


def test_parse_output_flags_ignores_middle_group_placement() -> None:
    """Intermediate group placement is not a supported output flag location."""
    assert output.parse(["auth", "--json", "ls"]) == output.OutputMode.HUMAN


def test_parse_output_flags_defaults_to_human() -> None:
    """No machine flags resolves to human output mode."""
    assert output.parse(["auth", "ls"]) == output.OutputMode.HUMAN


def test_parse_output_flags_top_level_only() -> None:
    """Top-level placement alone selects machine output mode."""
    assert output.parse(["--json", "auth", "ls"]) == output.OutputMode.JSON


def test_parse_output_flags_leaf_only() -> None:
    """Leaf placement alone selects machine output mode."""
    assert output.parse(["auth", "ls", "--yaml"]) == output.OutputMode.YAML


def test_parse_output_flags_same_mode_at_both_placements_is_idempotent() -> None:
    """Duplicate same-mode flags across placements remain idempotent."""
    assert output.parse(["--json", "ps", "--json"]) == output.OutputMode.JSON
    assert output.parse(["--yaml", "auth", "ls", "--yaml"]) == output.OutputMode.YAML


def test_parse_output_flags_duplicate_same_mode_at_top_level_is_idempotent() -> None:
    """Duplicate same-mode flags at one placement remain idempotent."""
    assert output.parse(["--json", "--json", "auth", "ls"]) == output.OutputMode.JSON


def test_parse_output_flags_conflicting_modes_exit_two() -> None:
    """Different machine modes across placements raise output.conflict."""
    with pytest.raises(output.OutputConflictError) as exc_info:
        output.parse(["--json", "ps", "--yaml"])

    assert exc_info.value.code == "output.conflict"
    assert exc_info.value.exit_code == output.OUTPUT_CONFLICT_EXIT_CODE


def test_parse_output_flags_conflicting_modes_at_top_level() -> None:
    """Different machine modes at the same placement raise output.conflict."""
    with pytest.raises(output.OutputConflictError) as exc_info:
        output.parse(["--json", "--yaml", "auth", "ls"])

    assert exc_info.value.code == "output.conflict"
    assert exc_info.value.exit_code == output.OUTPUT_CONFLICT_EXIT_CODE


def test_dto_dump_includes_null_fields() -> None:
    """DTO serialization keeps declared null fields for stable machine keys."""
    payload = dto_dump(SampleDto(name="cadc"))
    assert payload == {"name": "cadc", "optional": None}


def test_render_stdout_json_is_data_only() -> None:
    """JSON stdout rendering emits serialized data without diagnostics."""
    rendered = output.render_stdout({"idp": "cadc"}, output.OutputMode.JSON)
    assert json.loads(rendered) == {"idp": "cadc"}


def test_render_stdout_yaml_is_data_only() -> None:
    """YAML stdout rendering emits serialized data without diagnostics."""
    rendered = output.render_stdout({"idp": "cadc"}, output.OutputMode.YAML)
    assert yaml.safe_load(rendered) == {"idp": "cadc"}


def test_render_stdout_human_is_empty() -> None:
    """Human mode does not emit machine payloads on stdout."""
    assert output.render_stdout({"idp": "cadc"}, output.OutputMode.HUMAN) == ""


def test_render_stderr_error_json_on_stderr_channel() -> None:
    """JSON machine errors render structured payloads for stderr."""
    error = StructuredError(
        code="output.conflict",
        message="Conflicting output flags.",
        hint="Use only one of --json or --yaml.",
    )
    rendered = output.render_stderr_error(error, output.OutputMode.JSON)
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
    rendered = output.render_stderr_error(error, output.OutputMode.YAML)
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

    output.to_stdout({"sessions": []}, output.OutputMode.JSON)
    output.to_stderr(
        StructuredError(
            code="transport.failure",
            message="Request failed.",
        ),
        output.OutputMode.JSON,
    )

    assert json.loads(stdout.getvalue()) == {"sessions": []}
    assert json.loads(stderr.getvalue())["code"] == "transport.failure"
    assert stdout.getvalue().strip() != stderr.getvalue().strip()


def test_render_stdout_accepts_pydantic_dto() -> None:
    """Stdout rendering accepts DTO models via shared dump helpers."""
    rendered = output.render_stdout(
        SampleDto(name="srcnet", optional=None), output.OutputMode.JSON
    )
    assert json.loads(rendered) == {"name": "srcnet", "optional": None}
