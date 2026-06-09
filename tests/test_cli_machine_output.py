"""Tests for machine output on rollout CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import click
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()
_CADC_URI = "ivo://cadc.nrc.ca/skaha"

_AUTH_KEYS = frozenset({"idp", "name", "mode", "expiry", "active", "server"})


def _patch_config(path: Path):
    """Patch the persisted config path used by CLI commands."""
    return patch("canfar.models.config.CONFIG_PATH", path)


def _write_config(path: Path) -> None:
    """Write a minimal config fixture for machine-output tests."""
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


def test_auth_ls_human_mode_emits_banner(tmp_path: Path) -> None:
    """``auth ls`` in human mode emits the active-server banner."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls"])

    assert result.exit_code == 0
    assert result.stdout.startswith("@")


def test_auth_ls_json_stdout_is_data_only(tmp_path: Path) -> None:
    """``auth ls --json`` emits JSON on stdout without the human-mode banner."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls", "--json"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")
    json.loads(result.stdout)


def test_auth_group_flag_before_subcommand_is_rejected(tmp_path: Path) -> None:
    """Group-level ``--json``/``--yaml`` placement exits 2 with guidance."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        json_result = runner.invoke(cli, ["auth", "--json", "ls"])
        yaml_result = runner.invoke(cli, ["auth", "--yaml", "show"])

    assert json_result.exit_code == 2
    assert "Place --json or --yaml after the subcommand." in json_result.stderr
    assert yaml_result.exit_code == 2
    assert "Place --json or --yaml after the subcommand." in yaml_result.stderr


def test_ps_human_mode_emits_banner(tmp_path: Path) -> None:
    """Human-only commands like ``ps`` emit the active-server banner."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with (
        _patch_config(config_path),
        patch("canfar.cli.ps.AsyncSession") as session_cls,
    ):
        session = AsyncMock()
        session.fetch.return_value = []
        session_cls.return_value.__aenter__.return_value = session
        result = runner.invoke(cli, ["ps"])

    assert result.exit_code == 0
    assert result.stdout.startswith("@")


def test_auth_default_json_matches_show(tmp_path: Path) -> None:
    """Default ``auth`` emits the same payload as ``auth show --json``."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        default_result = runner.invoke(cli, ["auth", "--json"])
        show_result = runner.invoke(cli, ["auth", "show", "--json"])

    assert default_result.exit_code == 0
    assert show_result.exit_code == 0
    assert json.loads(default_result.stdout) == json.loads(show_result.stdout)


def test_auth_show_json_payload_shape(tmp_path: Path) -> None:
    """``auth show --json`` emits a domain Authentication object without envelopes."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "show", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert set(payload) == _AUTH_KEYS
    assert payload["idp"] == "cadc"
    assert payload["active"] is True


def test_auth_ls_json_payload_shape(tmp_path: Path) -> None:
    """``auth ls --json`` emits a JSON array of Authentication objects."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert len(payload) == 2
    assert all(set(item) == _AUTH_KEYS for item in payload)
    srcnet = next(item for item in payload if item["idp"] == "srcnet")
    assert "server" in srcnet
    assert srcnet["server"] is None


def test_root_json_flag_before_command_path_is_not_supported(
    tmp_path: Path,
) -> None:
    """Root ``--json`` is rejected; supported commands own machine output."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["--json", "auth", "ls"])

    assert result.exit_code == 2
    assert "--json" in click.unstyle(result.stderr)


def test_conflicting_output_flags_exit_two() -> None:
    """Conflicting machine output flags exit with code 2."""
    result = runner.invoke(cli, ["auth", "ls", "--json", "--yaml"])
    assert result.exit_code == 2
    assert "Conflicting machine output flags" in result.stderr


def test_unsupported_command_rejects_leaf_json_flag() -> None:
    """Commands without machine flags reject ``--json`` at the leaf."""
    result = runner.invoke(cli, ["auth", "purge", "--json", "--force"])
    assert result.exit_code == 2
    assert "--json" in click.unstyle(result.stderr)
