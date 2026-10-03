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
from canfar.models.http import (
    ResourceRange,
    Server,
    ServerResources,
    SessionResources,
)

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()
_CADC_URI = "ivo://cadc.nrc.ca/skaha"


def _patch_config(path: Path):
    return patch("canfar.models.config.CONFIG_PATH", path)


def _write_config(path: Path) -> None:
    data = {
        "version": 1,
        "active": {"authentication": "cadc", "server": "CADC-CANFAR"},
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
                "uri": _CADC_URI,
                "url": "https://ws-uv.canfar.net/skaha",
                "version": "v1",
                "auths": ["x509"],
            }
        },
    }
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_server_ls_lists_active_idp_servers(tmp_path: Path) -> None:
    """``server ls`` loads once and renders those known servers."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    known = Server(
        idp="cadc",
        name="CADC-CANFAR",
        uri=AnyUrl(_CADC_URI),
        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        version="v1",
        auths=["x509"],
    )

    with (
        _patch_config(config_path),
        patch("canfar.cli.server.auth_show") as show,
        patch("canfar.cli.server.server_list", return_value=[known]) as list_,
    ):
        result = runner.invoke(cli, ["server", "ls"])

    assert result.exit_code == 0
    assert "CADC-CANFAR" in result.stdout
    assert _CADC_URI in result.stdout
    show.assert_called_once_with()
    list_.assert_called_once_with()


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
    fetched = target.model_copy(
        update={"resources": ServerResources(sessions=3)}, deep=True
    )

    with (
        _patch_config(config_path),
        patch("canfar.server._validate_server", return_value=fetched),
    ):
        result = runner.invoke(cli, ["server", "use", _CADC_URI])

    assert result.exit_code == 0
    with _patch_config(config_path):
        saved = Configuration()
    assert saved.active.server == "CADC-CANFAR"


def test_server_use_selects_by_name(tmp_path: Path) -> None:
    """``server use`` resolves a Server Name selector and persists it."""
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
    fetched = target.model_copy(
        update={"resources": ServerResources(sessions=3)}, deep=True
    )

    with (
        _patch_config(config_path),
        patch("canfar.server._validate_server", return_value=fetched),
    ):
        result = runner.invoke(cli, ["server", "use", "CADC-CANFAR"])

    assert result.exit_code == 0
    with _patch_config(config_path):
        saved = Configuration()
    assert saved.active.server == "CADC-CANFAR"
    assert saved.active.servers["cadc"] == "CADC-CANFAR"


def test_server_ls_json_output(tmp_path: Path) -> None:
    """``server ls -o json`` emits a JSON array of Server objects on stdout."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["server", "ls", "-o", "json"])

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
        "storage",
        "resources",
    }
    assert server["uri"] == _CADC_URI
    assert server["resources"] is None


def test_server_ls_machine_output_includes_server_name(tmp_path: Path) -> None:
    """``server ls`` machine output exposes the Server Name config identity."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    with _patch_config(config_path):
        json_result = runner.invoke(cli, ["server", "ls", "--output", "json"])
        yaml_result = runner.invoke(cli, ["server", "ls", "--output", "yaml"])

    assert json_result.exit_code == 0
    assert json.loads(json_result.stdout)[0]["name"] == "CADC-CANFAR"
    assert yaml_result.exit_code == 0
    assert yaml.safe_load(yaml_result.stdout)[0]["name"] == "CADC-CANFAR"


def test_server_ls_shows_session_resources(tmp_path: Path) -> None:
    """Human ``server ls`` shows each Server's limits and marks unknown ones."""
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    limited = Server(
        idp="cadc",
        name="CADC-CANFAR",
        uri=AnyUrl(_CADC_URI),
        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        version="v1",
        resources=ServerResources(
            flexible=SessionResources(
                cores=ResourceRange(min=1, max=2),
                ram=ResourceRange(min=2, max=4),
            ),
            fixed=SessionResources(
                cores=ResourceRange(min=1, max=34),
                ram=ResourceRange(min=1, max=384),
            ),
            gpus=ResourceRange(min=0, max=0),
            sessions=5,
        ),
    )
    unknown = limited.model_copy(
        update={"name": "Legacy", "resources": None}, deep=True
    )

    with (
        _patch_config(config_path),
        patch("canfar.cli.server.auth_show"),
        patch("canfar.cli.server.server_list", return_value=[limited, unknown]),
    ):
        result = runner.invoke(cli, ["server", "ls"])

    assert result.exit_code == 0
    rows = [line.split() for line in result.stdout.splitlines()]
    assert [
        *("CADC-CANFAR", _CADC_URI, "v1"),
        *("1-2", "cores", "1-34", "cores", "none", "5"),
    ] in rows
    assert ["https://ws-uv.canfar.net/skaha", "2-4", "GB", "1-384", "GB"] in rows
    assert ["Legacy", _CADC_URI, "v1", *["unknown"] * 4] in rows
