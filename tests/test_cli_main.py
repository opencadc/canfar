"""Test main CLI entrypoint."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli

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


def test_human_cli_runs_when_active_server_is_null(tmp_path: Path) -> None:
    """Human-mode CLI remains usable when no active server is selected."""
    config_path = tmp_path / "config.yaml"
    _write_null_active_server_config(config_path)

    with patch("canfar.models.config.CONFIG_PATH", config_path):
        result = runner.invoke(cli, ["auth", "ls"])

    assert result.exit_code == 0
    assert result.stdout.startswith("@unknown")


def test_context_command_group_is_removed() -> None:
    """``canfar context`` is no longer a supported command group."""
    result = runner.invoke(cli, ["context", "show"])
    assert result.exit_code != 0
    assert "No such command 'context'" in result.output


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
