"""Tests for the `canfar config` CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import click
import yaml
from pydantic import BaseModel
from typer.testing import CliRunner

from canfar.cli.config import _format_value, config

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()

_CONFIG_KEYS = frozenset(
    {"version", "active", "authentication", "server", "registry", "console"}
)


def _patch_config_path(path: Path):
    """Patch package-level config path for CLI tests."""
    return patch.multiple(
        "canfar",
        CONFIG_PATH=path,
    )


def test_config_get_default_console_width(tmp_path: Path) -> None:
    """Default config exposes the console width through ``config get``."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["get", "console.width"])
        assert result.exit_code == 0
        assert result.stdout.strip().splitlines()[-1] == "120"


def test_config_set_and_get_console_width(tmp_path: Path) -> None:
    """Config set persists console width for later reads."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["set", "console.width", "130"])
        assert result.exit_code == 0

        result = runner.invoke(config, ["get", "console.width"])
        assert result.exit_code == 0
        assert result.stdout.strip().splitlines()[-1] == "130"

        assert config_path.exists()
        assert "width: 130" in config_path.read_text(encoding="utf-8")


def test_config_set_invalid_value_fails_validation(tmp_path: Path) -> None:
    """Invalid config values fail validation."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["set", "console.width", "not_an_int"])
        assert result.exit_code == 1


class ExampleModel(BaseModel):
    """Tiny model for config formatting tests."""

    value: int


def test_config_show_path_format_and_errors(tmp_path: Path) -> None:
    """Test config show/path/format helpers and handled error paths."""
    config_path = tmp_path / "config.yaml"

    with (
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["show"])

    assert result.exit_code == 0
    assert "'version': 1" in result.stdout

    result = runner.invoke(config, ["ls"])
    assert result.exit_code == 2
    assert "No such command 'ls'" in result.stderr

    result = runner.invoke(config, ["path"])
    assert result.exit_code == 0
    assert ".canfar" in result.stdout

    assert _format_value(ExampleModel(value=7)) == '{\n  "value": 7\n}'
    assert _format_value({"a": [1]}) == '{\n  "a": [\n    1\n  ]\n}'
    assert _format_value(None) == "null"

    with patch("canfar.cli.config.Configuration", side_effect=RuntimeError("bad")):
        result = runner.invoke(config, ["show"])

    assert result.exit_code == 1
    assert "bad" in result.stdout

    with patch("canfar.cli.config.Configuration") as cfg:
        cfg.return_value.get_value.side_effect = KeyError("missing")
        result = runner.invoke(config, ["get", "missing"])

    assert result.exit_code == 1
    assert "missing" in result.stdout

    with patch("canfar.cli.config.Configuration") as cfg:
        cfg.return_value.set_value.side_effect = TypeError("wrong")
        result = runner.invoke(config, ["set", "console.width", "120"])

    assert result.exit_code == 1
    assert "wrong" in result.stdout


def test_config_show_json_emits_configuration_model(tmp_path: Path) -> None:
    """``config show --json`` emits the Configuration model with stable keys."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["show", "--json"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")
    payload = json.loads(result.stdout)
    assert set(payload) == _CONFIG_KEYS
    assert payload["version"] == 1


def test_config_show_yaml_emits_configuration_model(tmp_path: Path) -> None:
    """``config show --yaml`` emits the Configuration model on stdout."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["show", "--yaml"])

    assert result.exit_code == 0
    payload = yaml.safe_load(result.stdout)
    assert set(payload) == _CONFIG_KEYS


def test_config_show_json_redacts_oidc_secrets(tmp_path: Path) -> None:
    """``config show --json`` must not emit raw OIDC secrets from saved auth."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.dump(
            {
                "version": 1,
                "active": {
                    "authentication": "srcnet",
                    "server": "ivo://cadc.nrc.ca/skaha",
                },
                "authentication": [
                    {
                        "idp": "srcnet",
                        "mode": "oidc",
                        "endpoints": {},
                        "client": {"identity": "client-id", "secret": "raw-secret"},
                        "token": {
                            "access": "raw-access",
                            "refresh": "raw-refresh",
                        },
                        "expiry": {},
                    }
                ],
                "server": [
                    {
                        "idp": "srcnet",
                        "name": "test",
                        "uri": "ivo://cadc.nrc.ca/skaha",
                        "url": "https://example.test/skaha",
                        "version": "v1",
                        "auths": ["oidc"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["show", "--json"])

    assert result.exit_code == 0
    rendered = result.stdout
    assert "raw-secret" not in rendered
    assert "raw-access" not in rendered
    assert "raw-refresh" not in rendered
    oidc = json.loads(rendered)["authentication"][0]
    assert oidc["client"]["identity"] == "client-id"
    assert oidc["client"]["secret"] == "**********"
    assert oidc["token"]["access"] == "**********"
    assert oidc["token"]["refresh"] == "**********"


def test_config_show_json_keeps_null_secrets_null(tmp_path: Path) -> None:
    """Unset OIDC secret fields stay null (stable keys, no fake masking)."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.dump(
            {
                "version": 1,
                "active": {
                    "authentication": "srcnet",
                    "server": "ivo://cadc.nrc.ca/skaha",
                },
                "authentication": [
                    {
                        "idp": "srcnet",
                        "mode": "oidc",
                        "endpoints": {},
                        "client": {"identity": "client-id"},
                        "token": {},
                        "expiry": {},
                    }
                ],
                "server": [
                    {
                        "idp": "srcnet",
                        "name": "test",
                        "uri": "ivo://cadc.nrc.ca/skaha",
                        "url": "https://example.test/skaha",
                        "version": "v1",
                        "auths": ["oidc"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["show", "--json"])

    assert result.exit_code == 0
    oidc = json.loads(result.stdout)["authentication"][0]
    assert oidc["client"]["secret"] is None
    assert oidc["token"]["access"] is None
    assert oidc["token"]["refresh"] is None


def test_config_get_json_emits_scalar_value(tmp_path: Path) -> None:
    """``config get --json`` emits the resolved value without human formatting."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["get", "console.width", "--json"])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")
    assert json.loads(result.stdout) == 120


def test_config_get_yaml_emits_scalar_value(tmp_path: Path) -> None:
    """``config get --yaml`` emits the resolved scalar value on stdout."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["get", "console.width", "--yaml"])

    assert result.exit_code == 0
    assert yaml.safe_load(result.stdout) == 120


def test_config_get_json_redacts_sensitive_paths(tmp_path: Path) -> None:
    """``config get --json`` masks sensitive OIDC credential values."""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.dump(
            {
                "version": 1,
                "active": {
                    "authentication": "srcnet",
                    "server": "ivo://cadc.nrc.ca/skaha",
                },
                "authentication": [
                    {
                        "idp": "srcnet",
                        "mode": "oidc",
                        "endpoints": {},
                        "client": {"identity": "client-id", "secret": "raw-secret"},
                        "token": {"access": "raw-access", "refresh": "raw-refresh"},
                        "expiry": {},
                    }
                ],
                "server": [
                    {
                        "idp": "srcnet",
                        "name": "test",
                        "uri": "ivo://cadc.nrc.ca/skaha",
                        "url": "https://example.test/skaha",
                        "version": "v1",
                        "auths": ["oidc"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(
            config,
            ["get", "authentication.0.client.secret", "--json"],
        )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == "**********"
    assert "raw-secret" not in result.stdout


def test_config_help_uses_config_command_descriptions() -> None:
    """Config help exposes the canonical command descriptions."""
    result = runner.invoke(config, ["--help"])
    help_text = click.unstyle(result.stdout)

    assert result.exit_code == 0
    assert "show  Display client configuration" in help_text
    assert "get   Retrieve a config value." in help_text
    assert "set   Set a config value." in help_text
    assert "path  Local path of config" in help_text
