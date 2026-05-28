"""Tests for the ``canfar auth`` CLI commands."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from unittest.mock import patch

import humanize
import yaml
from typer.testing import CliRunner

from canfar.authentication import Authentication
from canfar.cli.auth import auth
from canfar.cli.main import cli
from canfar.models.config import Configuration

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
            },
            {
                "idp": "srcnet",
                "name": "SRCNet",
                "uri": "ivo://srcnet.example/skaha",
                "url": "https://srcnet.example/skaha",
                "version": "v1",
                "auths": ["oidc"],
            },
        ],
    }
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_auth_default_shows_active_authentication(tmp_path: Path) -> None:
    """Default ``canfar auth`` behaves like ``auth show``."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(auth, [])

    assert result.exit_code == 0
    assert "cadc" in result.stdout


def test_auth_show_humanizes_expiry() -> None:
    """Human ``auth show`` output displays a relative expiry time."""
    future = time.time() + 86400 * 30
    record = Authentication(
        idp="cadc",
        name="Canadian Astronomy Data Centre",
        mode="x509",
        expiry=future,
        active=True,
        server="ivo://cadc.nrc.ca/skaha",
    )
    expected = humanize.naturaltime(datetime.fromtimestamp(future, tz=timezone.utc))

    with patch("canfar.cli.auth.auth_show", return_value=record):
        result = runner.invoke(auth, ["show"])

    assert result.exit_code == 0
    assert expected in result.stdout
    assert str(future) not in result.stdout


def test_auth_ls_lists_saved_records(tmp_path: Path) -> None:
    """``auth ls`` lists saved Authentication records."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(auth, ["ls"])

    assert result.exit_code == 0
    assert "cadc" in result.stdout
    assert "srcnet" in result.stdout


def test_auth_use_switches_by_idp(tmp_path: Path) -> None:
    """``auth use`` selects Authentication by canonical IDP key."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with (
        _patch_config(config_path),
        patch("canfar.cli.auth._validate_server") as mock_validate,
    ):
        mock_validate.side_effect = lambda server: server
        result = runner.invoke(auth, ["use", "srcnet"])

    assert result.exit_code == 0
    with _patch_config(config_path):
        saved = Configuration()
    assert saved.active.authentication == "srcnet"


def test_auth_remove_requires_force_for_active_idp(tmp_path: Path) -> None:
    """Removing the active IDP requires confirmation or ``--force``."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(auth, ["rm", "cadc"], input="n\n")

    assert result.exit_code == 0
    assert "cancelled" in result.stdout.lower()


def test_auth_remove_force_removes_active_idp(tmp_path: Path) -> None:
    """``auth rm --force`` removes the active IDP and associated servers."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(auth, ["rm", "cadc", "--force"])

    assert result.exit_code == 0
    with _patch_config(config_path):
        saved = Configuration()
    assert all(item.idp != "cadc" for item in saved.authentication)
    assert all(item.idp != "cadc" for item in saved.server)


def test_auth_purge_requires_force(tmp_path: Path) -> None:
    """``auth purge`` requires ``--force``."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(auth, ["purge"])

    assert result.exit_code == 1


def test_auth_purge_force_preserves_registry_and_console(tmp_path: Path) -> None:
    """``auth purge --force`` resets auth/server while preserving other settings."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        before = Configuration()
        before.console = before.console.model_copy(update={"width": 99})
        before.save()
        result = runner.invoke(auth, ["purge", "--force"])

    assert result.exit_code == 0
    with _patch_config(config_path):
        after = Configuration()
    assert after.console.width == 99


def test_authentication_alias_is_wired(tmp_path: Path) -> None:
    """``canfar authentication`` aliases ``canfar auth``."""
    config_path = tmp_path / "config.yaml"
    _write_v1_config(config_path)

    with _patch_config(config_path):
        result = runner.invoke(cli, ["authentication"])

    assert result.exit_code == 0
    assert "cadc" in result.stdout
