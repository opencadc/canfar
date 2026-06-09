"""Tests for the ``canfar server`` CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import yaml
from pydantic import AnyHttpUrl, AnyUrl
from typer.testing import CliRunner

from canfar.cli.main import cli
from canfar.models.config import Configuration
from canfar.models.http import Server

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()
_CADC_URI = "ivo://cadc.nrc.ca/skaha"


def _patch_config(path: Path):
    return patch("canfar.models.config.CONFIG_PATH", path)


def _write_config(path: Path) -> None:
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


def test_server_ls_lists_active_idp_servers(tmp_path: Path) -> None:
    """``server ls`` renders known servers for the active IDP."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["server", "ls"])

    assert result.exit_code == 0
    assert "CADC-CANFAR" in result.stdout
    assert _CADC_URI in result.stdout


def test_server_use_selects_by_uri(tmp_path: Path) -> None:
    """``server use`` accepts a server URI selector."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    target = Server(
        idp="cadc",
        name="CADC-CANFAR",
        uri=AnyUrl(_CADC_URI),
        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        version="v1",
        auths=["x509"],
    )
    fetched = target.model_copy(update={"cores": 8, "ram": 64}, deep=True)

    with (
        _patch_config(config_path),
        patch("canfar.server._validate_server", return_value=fetched),
    ):
        result = runner.invoke(cli, ["server", "use", _CADC_URI])

    assert result.exit_code == 0
    with _patch_config(config_path):
        saved = Configuration()
    assert str(saved.active.server) == _CADC_URI


def test_server_ls_json_output(tmp_path: Path) -> None:
    """``server ls --json`` emits a JSON array of Server objects on stdout."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["server", "ls", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert isinstance(payload, list)
    assert len(payload) == 1
    server = payload[0]
    assert set(server) == {
        "name",
        "uri",
        "url",
        "version",
        "auths",
        "idp",
        "cores",
        "ram",
        "gpus",
        "status",
    }
    assert server["uri"] == _CADC_URI
    assert server["name"] == "CADC-CANFAR"
    assert server["status"] is None
