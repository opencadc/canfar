"""Tests for the `canfar config` CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from typer.testing import CliRunner

from canfar.cli.config import config

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


def _patch_config_path(path: Path):
    return patch.multiple(
        "canfar",
        CONFIG_PATH=path,
    )


def test_config_get_default_console_width(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["get", "console.width"])
        assert result.exit_code == 0
        assert result.stdout.strip() == "120"


def test_config_set_and_get_console_width(tmp_path: Path) -> None:
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
        assert result.stdout.strip() == "130"

        assert config_path.exists()
        assert "width: 130" in config_path.read_text(encoding="utf-8")


def test_config_set_invalid_value_fails_validation(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.config.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(config, ["set", "console.width", "not_an_int"])
        assert result.exit_code == 1
