"""Tests for machine output on rollout CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()
_CADC_URI = "ivo://cadc.nrc.ca/skaha"


def _patch_config(path: Path):
    return patch("canfar.models.config.CONFIG_PATH", path)


def _write_v1_config(path: Path) -> None:
    data = {
        "version": 1,
        "active": {"authentication": "cadc", "server": _CADC_URI},
        "authentication": [
            {
                "idp": "cadc",
                "mode": "x509",
                "path": "/saved/cadc.pem",
                "expiry": 123.0,
            },
            {
                "idp": "srcnet",
                "mode": "oidc",
                "endpoints": {},
                "client": {},
                "token": {},
                "expiry": {},
            },
        ],
        "server": [
            {
                "idp": "cadc",
                "name": "CADC-CANFAR",
                "uri": _CADC_URI,
                "url": "https://ws-uv.canfar.net/skaha",
                "version": "v1",
                "auths": ["x509"],
            }
        ],
    }
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_auth_ls_json_stdout_is_data_only(tmp_path: Path) -> None:
    """``auth ls --json`` emits JSON on stdout without the human-mode banner."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls", "--json"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")
    json.loads(result.stdout)


def test_auth_default_json_matches_show(tmp_path: Path) -> None:
    """Default ``auth`` emits the same payload as ``auth show --json``."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        default_result = runner.invoke(cli, ["auth", "--json"])
        show_result = runner.invoke(cli, ["auth", "show", "--json"])

    assert default_result.exit_code == 0
    assert show_result.exit_code == 0
    assert json.loads(default_result.stdout) == json.loads(show_result.stdout)


def test_auth_ls_json_includes_null_fields(tmp_path: Path) -> None:
    """``auth ls --json`` keeps declared null DTO fields."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    srcnet = next(
        item for item in payload["authentications"] if item["idp"] == "srcnet"
    )
    assert "server" in srcnet
    assert srcnet["server"] is None


def test_top_level_json_flag_before_command_path(tmp_path: Path) -> None:
    """Top-level ``--json`` before the command path is supported."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["--json", "auth", "ls"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "authentications" in payload


def test_conflicting_output_flags_exit_two() -> None:
    """Conflicting machine output flags exit with code 2."""
    result = runner.invoke(cli, ["--json", "auth", "ls", "--yaml"])
    assert result.exit_code == 2


def test_unsupported_machine_output_exit_one() -> None:
    """Unsupported machine output commands exit 1 with exact stderr text."""
    result = runner.invoke(cli, ["--json", "auth", "purge", "--force"])
    assert result.exit_code == 1
    assert "machine output not supported for this command yet" in result.stderr
    assert "use default human output for now" in result.stderr
