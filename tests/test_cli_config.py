"""Tests for the `canfar config` CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from pydantic import BaseModel
from typer.testing import CliRunner

from canfar.cli.config import _format_value, config

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
