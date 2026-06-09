"""Tests for CLI machine output infrastructure."""

from __future__ import annotations

import json
from io import StringIO

import pytest
import typer
import yaml
from pydantic import BaseModel

from canfar.authentication import Authentication
from canfar.cli import machine, output
from canfar.errors import StructuredError
from canfar.models.http import Server


class SampleModel(BaseModel):
    """Sample model for serialization tests."""

    name: str
    optional: str | None = None


def test_output_mode_values() -> None:
    """OutputMode exposes human, json, and yaml members."""
    assert output.OutputMode.HUMAN.value == "human"
    assert output.OutputMode.JSON.value == "json"
    assert output.OutputMode.YAML.value == "yaml"


def test_resolve_mode_defaults_to_human() -> None:
    """No machine flags resolve to human output mode."""
    assert machine.resolve_mode(json_output=False, yaml_output=False) == (
        output.OutputMode.HUMAN
    )


def test_resolve_mode_json_and_yaml() -> None:
    """Single machine flags select the matching output mode."""
    assert machine.resolve_mode(json_output=True, yaml_output=False) == (
        output.OutputMode.JSON
    )
    assert machine.resolve_mode(json_output=False, yaml_output=True) == (
        output.OutputMode.YAML
    )


def test_resolve_mode_conflict_exits_two() -> None:
    """Conflicting machine output flags exit with code 2."""
    with pytest.raises(typer.Exit) as exc_info:
        machine.resolve_mode(json_output=True, yaml_output=True)
    assert exc_info.value.exit_code == output.OUTPUT_CONFLICT_EXIT_CODE


def test_model_dump_includes_null_fields() -> None:
    """Serialization keeps declared null fields for stable machine keys."""
    payload = output.render_stdout(
        Authentication(
            idp="cadc",
            name="CADC",
            mode="x509",
            expiry=None,
            active=True,
            server=None,
        ),
        output.OutputMode.JSON,
    )
    parsed = json.loads(payload)
    assert set(parsed) == {"idp", "name", "mode", "expiry", "active", "server"}
    assert parsed["server"] is None


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

    output.to_stdout([{"id": "s1"}], output.OutputMode.JSON)
    output.to_stderr(
        StructuredError(
            code="transport.failure",
            message="Request failed.",
        ),
        output.OutputMode.JSON,
    )

    assert json.loads(stdout.getvalue()) == [{"id": "s1"}]
    assert json.loads(stderr.getvalue())["code"] == "transport.failure"
    assert stdout.getvalue().strip() != stderr.getvalue().strip()


def test_render_stdout_accepts_pydantic_model() -> None:
    """Stdout rendering accepts Pydantic models via model_dump."""
    rendered = output.render_stdout(
        SampleModel(name="srcnet", optional=None), output.OutputMode.JSON
    )
    assert json.loads(rendered) == {"name": "srcnet", "optional": None}


def test_render_stdout_accepts_model_list() -> None:
    """Stdout rendering serializes lists of Pydantic models."""
    rendered = output.render_stdout(
        [
            Server(name="CADC", status=None),
            Server(name="SRC", status=None),
        ],
        output.OutputMode.JSON,
    )
    payload = json.loads(rendered)
    assert len(payload) == 2
    assert payload[0]["name"] == "CADC"
    assert "status" in payload[0]
    assert payload[0]["status"] is None
