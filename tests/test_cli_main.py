"""Test main CLI entrypoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


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
