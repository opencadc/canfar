"""Tests for the `canfar auth` CLI commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from canfar.cli.auth import auth

runner = CliRunner()


def _patch_config_path(path: Path):
    return patch.multiple(
        "canfar",
        CONFIG_PATH=path,
    )


def test_auth_commands():
    """Test `canfar auth` commands."""
    config_path = Path(".pytest-cache") / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.auth.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(auth, ["--help"])
        assert result.exit_code == 0
        results = runner.invoke(auth, ["login", "--help"])
        assert results.exit_code == 0
        result = runner.invoke(auth, ["list", "--help"])
        assert result.exit_code == 0
        result = runner.invoke(auth, ["list"])
        assert result.exit_code == 0
        results = runner.invoke(auth, ["switch", "--help"])
        assert results.exit_code == 0
        results = runner.invoke(auth, ["use", "--help"])
        assert results.exit_code == 0
        results = runner.invoke(auth, ["use", "doesnt-exist"])
        assert results.exit_code == 1
        result = runner.invoke(auth, ["remove", "--help"])
        assert result.exit_code == 0
        result = runner.invoke(auth, ["rm", "--help"])
        assert result.exit_code == 0
        result = runner.invoke(auth, ["rm", "doesnt-exist"])
        assert result.exit_code == 1
        results = runner.invoke(auth, ["purge", "--help"])
        assert results.exit_code == 0
        result = runner.invoke(auth, ["purge", "-y"])
        assert result.exit_code == 0


def test_auth_list(tmp_path: Path):
    """Test `canfar auth list` command."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.auth.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(auth, ["list"])
        assert result.exit_code == 0


def test_auth_switch(tmp_path: Path):
    """Test `canfar auth switch` command."""
    config_path = tmp_path / "config.yaml"
    with (
        _patch_config_path(config_path),
        patch("canfar.cli.auth.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(auth, ["switch", "default"])
        assert result.exit_code == 0
