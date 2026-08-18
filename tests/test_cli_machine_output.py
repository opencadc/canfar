"""Tests for machine output on rollout CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import click
import pytest
import yaml
from typer.testing import CliRunner

from canfar.cli.main import cli

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

runner = CliRunner()
_CADC_URI = "ivo://cadc.nrc.ca/skaha"

_AUTH_KEYS = frozenset({"idp", "name", "mode", "expiry", "active", "server"})


def _patch_config(path: Path):
    """Patch the persisted config path used by CLI commands."""
    return patch("canfar.models.config.CONFIG_PATH", path)


def _write_config(path: Path, *, banner: bool | None = None) -> None:
    """Write a minimal config fixture for machine-output tests."""
    data = {
        "version": 1,
        "active": {"authentication": "cadc", "server": "CADC-CANFAR"},
        "authentication": {
            "cadc": {
                "mode": "x509",
                "path": "/saved/cadc.pem",
                "expiry": 123.0,
            },
            "srcnet": {
                "mode": "oidc",
                "endpoints": {},
                "client": {},
                "token": {},
                "expiry": {},
            },
        },
        "servers": {
            "CADC-CANFAR": {
                "idp": "cadc",
                "uri": _CADC_URI,
                "url": "https://ws-uv.canfar.net/skaha",
                "version": "v1",
                "auths": ["x509"],
            }
        },
    }
    if banner is not None:
        data["console"] = {"banner": banner}
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_auth_ls_human_mode_emits_banner(tmp_path: Path) -> None:
    """``auth ls`` in human mode emits the active-server banner."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls"])

    assert result.exit_code == 0
    assert result.stdout.startswith("@")


def test_nested_image_command_emits_banner(tmp_path: Path) -> None:
    """Nested human commands emit the banner at terminal dispatch."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with (
        _patch_config(config_path),
        patch("canfar.cli.image.Images.details", return_value=[]),
    ):
        result = runner.invoke(cli, ["image", "ls"])

    assert result.exit_code == 0
    assert result.stdout.startswith("@CADC-CANFAR")


def test_config_can_disable_human_banner(tmp_path: Path) -> None:
    """``console.banner=false`` keeps human CLI stdout banner-free."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        set_result = runner.invoke(
            cli,
            ["config", "set", "console.banner", "false"],
        )
        command_result = runner.invoke(cli, ["auth", "ls"])
        enable_result = runner.invoke(
            cli,
            ["config", "set", "console.banner", "true"],
        )
        enabled_command_result = runner.invoke(cli, ["auth", "ls"])

    assert set_result.exit_code == 0
    assert command_result.exit_code == 0
    assert not command_result.stdout.startswith("@")
    assert enable_result.exit_code == 0
    assert enabled_command_result.exit_code == 0
    assert enabled_command_result.stdout.startswith("@")


def test_invalid_console_banner_value_fails_validation(tmp_path: Path) -> None:
    """``console.banner`` accepts only values Pydantic can parse as booleans."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(
            cli,
            ["config", "set", "console.banner", "sometimes"],
        )

    assert result.exit_code == 1


@pytest.mark.parametrize(
    ("flag", "parser"),
    [
        (["-o", "json"], json.loads),
        (["--output", "json"], json.loads),
        (["-o", "yaml"], yaml.safe_load),
        (["--output", "yaml"], yaml.safe_load),
    ],
)
@pytest.mark.parametrize("banner", [True, False])
def test_auth_ls_machine_stdout_is_data_only(
    tmp_path: Path,
    flag: list[str],
    parser: Callable[[str], object],
    banner: bool,
) -> None:
    """Machine flags always suppress the human banner configuration."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path, banner=banner)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls", *flag])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")
    parser(result.stdout)


@pytest.mark.parametrize(
    ("option", "parser"),
    [
        (["-o", "json"], json.loads),
        (["--output", "json"], json.loads),
        (["-o", "yaml"], yaml.safe_load),
        (["--output", "yaml"], yaml.safe_load),
    ],
)
def test_auth_ls_output_option_is_data_only(
    tmp_path: Path,
    option: list[str],
    parser: Callable[[str], object],
) -> None:
    """The leaf output option emits the filtered auth result as data only."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls", *option])

    assert result.exit_code == 0
    assert not result.stdout.startswith("@")
    assert result.stderr == ""
    parser(result.stdout)


@pytest.mark.parametrize("legacy", ["--json", "--yaml"])
def test_auth_ls_legacy_machine_switch_is_removed(legacy: str) -> None:
    """The former format-specific switches are no longer leaf options."""
    result = runner.invoke(cli, ["auth", "ls", legacy])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert legacy in click.unstyle(result.stderr)


def test_auth_ls_invalid_output_format_is_rejected() -> None:
    """Output formats are validated at the CLI boundary."""
    result = runner.invoke(cli, ["auth", "ls", "--output", "toml"])

    assert result.exit_code == 2
    assert result.stdout == ""
    assert "Invalid value" in click.unstyle(result.stderr)


def test_auth_group_output_option_before_subcommand_is_rejected() -> None:
    """The output option belongs to the emitting leaf command only."""
    result = runner.invoke(cli, ["auth", "--output", "json", "ls"])

    assert result.exit_code == 2
    assert "--output" in click.unstyle(result.stderr)


def test_passthrough_output_options_keep_human_banner(tmp_path: Path) -> None:
    """Output-looking container arguments remain verbatim after ``--``."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(
            cli,
            [
                "create",
                "--dry-run",
                "headless",
                "example.invalid/image",
                "--",
                "echo",
                "-o",
                "yaml",
                "--output",
                "json",
            ],
        )

    assert result.exit_code == 0
    assert result.stdout.startswith("@CADC-CANFAR")
    assert "Arguments: -o yaml --output json" in result.stdout


@pytest.mark.parametrize("name", ["--output", "--json"])
def test_machine_flag_spelling_as_option_value_keeps_human_banner(
    tmp_path: Path,
    name: str,
) -> None:
    """Machine flag spellings used as values leave output in human mode."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(
            cli,
            [
                "create",
                "--dry-run",
                "headless",
                "example.invalid/image",
                "--name",
                name,
            ],
        )

    assert result.exit_code == 0
    assert result.stdout.startswith("@CADC-CANFAR")
    assert f"Name: {name}" in result.stdout


def test_auth_group_flag_before_subcommand_is_rejected(tmp_path: Path) -> None:
    """Group-level output placement exits 2 with guidance."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        json_result = runner.invoke(cli, ["auth", "-o", "json", "ls"])
        yaml_result = runner.invoke(cli, ["auth", "--output", "yaml", "show"])

    assert json_result.exit_code == 2
    assert "Place --output json or --output yaml after the subcommand." in (
        json_result.stderr
    )
    assert yaml_result.exit_code == 2
    assert "Place --output json or --output yaml after the subcommand." in (
        yaml_result.stderr
    )


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
    """Default ``auth`` emits the same payload as ``auth show -o json``."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        default_result = runner.invoke(cli, ["auth", "-o", "json"])
        show_result = runner.invoke(cli, ["auth", "show", "-o", "json"])

    assert default_result.exit_code == 0
    assert show_result.exit_code == 0
    assert json.loads(default_result.stdout) == json.loads(show_result.stdout)


def test_auth_show_json_payload_shape(tmp_path: Path) -> None:
    """``auth show -o json`` emits a domain Authentication object without envelopes."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "show", "-o", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert set(payload) == _AUTH_KEYS
    assert payload["idp"] == "cadc"
    assert payload["active"] is True


def test_auth_ls_json_payload_shape(tmp_path: Path) -> None:
    """``auth ls -o json`` emits a JSON array of Authentication objects."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["auth", "ls", "-o", "json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert len(payload) == 2
    assert all(set(item) == _AUTH_KEYS for item in payload)
    srcnet = next(item for item in payload if item["idp"] == "srcnet")
    assert "server" in srcnet
    assert srcnet["server"] is None


def test_root_output_option_before_command_path_is_not_supported(
    tmp_path: Path,
) -> None:
    """Root output options are rejected; supported commands own machine output."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["-o", "json", "auth", "ls"])

    assert result.exit_code == 2
    assert "-o" in click.unstyle(result.stderr)


def test_unsupported_command_rejects_leaf_json_flag() -> None:
    """Commands without machine flags reject ``--json`` at the leaf."""
    result = runner.invoke(cli, ["auth", "purge", "--json", "--force"])
    assert result.exit_code == 2
    assert "--json" in click.unstyle(result.stderr)
