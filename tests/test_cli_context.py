"""Tests for the ``canfar context`` CLI commands."""

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
            }
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


def test_context_show_displays_active_state(tmp_path: Path) -> None:
    """``context show`` renders active Authentication and Server state."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["context", "show"])

    assert result.exit_code == 0
    assert "cadc" in result.stdout
    assert "CADC-CANFAR" in result.stdout


def test_context_ls_lists_compatible_pairs(tmp_path: Path) -> None:
    """``context ls`` lists saved Authentication and Server pairs."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["context", "ls"])

    assert result.exit_code == 0
    assert "cadc" in result.stdout
    assert "CADC-CANFAR" in result.stdout


def test_context_show_json_output(tmp_path: Path) -> None:
    """``context show --json`` emits DTO payloads on stdout."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["context", "show", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["authentication"]["idp"] == "cadc"
    assert payload["server"]["uri"] == _CADC_URI
