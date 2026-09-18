"""Test main CLI entrypoint."""

from __future__ import annotations

import json
import logging
import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli, main
from canfar.config.migration import ConfigResetRequiredError
from canfar.exceptions.context import AuthContextError, AuthExpiredError

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

_LOG_MESSAGES = {
    logging.DEBUG: "logging-contract-debug",
    logging.INFO: "logging-contract-info",
    logging.WARNING: "logging-contract-warning",
    logging.ERROR: "logging-contract-error",
    logging.CRITICAL: "logging-contract-critical",
}


@cli.command("logging-contract-probe", hidden=True)
def _logging_contract_probe() -> None:
    """Emit one message at each supported level through the public CLI runtime."""
    logger = logging.getLogger("canfar.contract")
    for level, message in _LOG_MESSAGES.items():
        logger.log(level, message)


def _write_null_active_server_config(path: Path) -> None:
    data = {
        "version": 1,
        "active": {"authentication": "cadc", "server": None},
        "authentication": {
            "cadc": {
                "mode": "x509",
                "path": "/saved/cadc.pem",
                "expiry": 123.0,
            }
        },
        "servers": {
            "CADC-CANFAR": {
                "idp": "cadc",
                "uri": "ivo://cadc.nrc.ca/skaha",
                "url": "https://ws-uv.canfar.net/skaha",
                "version": "v1",
                "auths": ["x509"],
            }
        },
    }
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_main_cli_no_subcommand() -> None:
    """Test main CLI entrypoint with no subcommand."""
    result = runner.invoke(cli)
    assert result.exit_code == 0


def test_main_cli_with_help_option() -> None:
    """Test main CLI entrypoint with --help option."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0


def test_nested_help_does_not_emit_banner() -> None:
    """Nested help remains free of command output decoration."""
    result = runner.invoke(cli, ["config", "--help"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")


def test_short_nested_help_does_not_emit_banner() -> None:
    """Nested short help remains free of command output decoration."""
    result = runner.invoke(cli, ["create", "-h"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")


def test_implicit_nested_help_does_not_emit_banner() -> None:
    """Bare nested groups keep implicit help free of command output."""
    result = runner.invoke(cli, ["config"])

    assert result.exit_code == 2
    assert not result.stdout.startswith("@")


def test_human_cli_runs_when_active_server_is_null(tmp_path: Path) -> None:
    """Human-mode CLI remains usable when no active server is selected."""
    config_path = tmp_path / "config.yaml"
    _write_null_active_server_config(config_path)

    with patch("canfar.models.config.CONFIG_PATH", config_path):
        result = runner.invoke(cli, ["auth", "ls"])

    assert result.exit_code == 0
    assert result.stdout.startswith("@unknown")


def test_version_debug_retains_bug_report_diagnostics() -> None:
    """The domain-specific version flag remains separate from root logging."""
    result = runner.invoke(cli, ["version", "--debug"])

    assert result.exit_code == 0, result.output
    assert "CANFAR Python Client Debug Information" in result.output
    assert "Python Version" in result.output


@pytest.mark.parametrize(
    ("root_options", "env_level", "minimum_level"),
    [
        ([], None, logging.CRITICAL),
        (["-v"], None, logging.ERROR),
        (["-vv"], None, logging.WARNING),
        (["-vvv"], None, logging.INFO),
        (["-vvvv"], None, logging.DEBUG),
        (["-vvvvv"], None, logging.DEBUG),
        ([], "info", logging.INFO),
        (["-v"], "chatty", logging.ERROR),
        (["--log-level", "warning", "-vvvv"], "chatty", logging.WARNING),
    ],
)
def test_root_logging_controls_emit_only_the_effective_levels(
    root_options: list[str],
    env_level: str | None,
    minimum_level: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Root controls apply CLI, environment, and packaged-default precedence."""
    if env_level is None:
        monkeypatch.delenv("CANFAR_LOGLEVEL", raising=False)
    else:
        monkeypatch.setenv("CANFAR_LOGLEVEL", env_level)

    result = runner.invoke(cli, [*root_options, "logging-contract-probe"])

    assert result.exit_code == 0, result.output
    for level, message in _LOG_MESSAGES.items():
        assert result.stdout.count(message) == 0
        assert result.stderr.count(message) == int(level >= minimum_level)


def test_invalid_logging_environment_fails_with_actionable_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An invalid known logging value fails before command execution."""
    monkeypatch.setenv("CANFAR_LOGLEVEL", "chatty")

    result = runner.invoke(cli, ["logging-contract-probe"])

    assert result.exit_code != 0
    assert "logging.invalid_env_value" in result.output
    assert "env_var=CANFAR_LOGLEVEL" in result.output
    assert "provided_value=chatty" in result.output
    assert "expected=critical,error,warning,info,debug" in result.output


def test_main_without_login_fails_as_not_authenticated(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A human-text command with no saved credential names the fix and exits 1."""
    monkeypatch.setattr(sys, "argv", ["canfar", "image", "ls"])

    with pytest.raises(SystemExit) as stopped:
        main()

    assert stopped.value.code == 1
    captured = capsys.readouterr()
    assert "Not authenticated" in captured.err
    assert "canfar login" in captured.err
    assert "Traceback" not in captured.err


def test_ps_machine_output_without_login_reports_authentication_required(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Machine mode reports the same condition with its stable error code."""
    monkeypatch.setattr(sys, "argv", ["canfar", "ps", "-o", "json"])

    with pytest.raises(SystemExit) as stopped:
        main()

    assert stopped.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["code"] == "authentication.required"


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (AuthContextError("cadc", "X.509 certificate cannot be used."), "invalid"),
        (AuthExpiredError("x509", "auth expired"), "expired"),
        (
            ConfigResetRequiredError("config.reset_required", "reset needed"),
            "reset needed",
        ),
    ],
)
def test_main_exits_nonzero_for_boundary_errors(
    error: Exception,
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Every handled boundary error is printed to stderr and exits 1 cleanly."""
    with (
        patch("canfar.cli.main.cli", side_effect=error),
        pytest.raises(SystemExit) as stopped,
    ):
        main()

    assert stopped.value.code == 1
    captured = capsys.readouterr()
    assert expected in captured.err
    assert captured.out == ""


def test_main_keeps_machine_errors_structured(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unrendered boundary error in machine mode stays parseable on stderr."""
    monkeypatch.setattr(sys, "argv", ["canfar", "server", "ls", "-o", "json"])
    error = AuthExpiredError("x509", "auth expired")

    with patch("canfar.cli.main.cli", side_effect=error), pytest.raises(SystemExit):
        main()

    payload = json.loads(capsys.readouterr().err)
    assert payload["code"] == "authentication.expired"
    assert "canfar login" in payload["hint"]
