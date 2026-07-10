"""Tests for the top-level ``canfar login`` CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from pydantic import AnyHttpUrl, AnyUrl
from typer.testing import CliRunner

from canfar.cli.main import cli
from canfar.models.auth import X509Credential
from canfar.models.config import Configuration
from canfar.models.http import Server

runner = CliRunner()
_CADC_URI = "ivo://cadc.nrc.ca/skaha"


def _patch_config(path: Path):
    return patch.multiple(
        "canfar",
        CONFIG_PATH=path,
    )


def _write_config(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data), encoding="utf-8")


def _merge_servers(config: Configuration, discovered: list[Server], idp: str) -> None:  # noqa: ARG001
    for server in discovered:
        if server.name is not None:
            config.servers[server.name] = server


def test_login_help_is_available() -> None:
    """Top-level login exposes help text."""
    result = runner.invoke(cli, ["login", "--help"])
    assert result.exit_code == 0
    assert "Login to CANFAR Science Platform" in result.stdout


def test_login_without_config_file_does_not_require_force(tmp_path: Path) -> None:
    """Default in-memory credentials do not block first login."""
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(
        idp="cadc",
        path=Path("/new/cert.pem"),
        expiry=456.0,
    )
    discovered = [
        Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri=AnyUrl(_CADC_URI),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]
    validated = discovered[0].model_copy(deep=True)

    with (
        _patch_config(config_path),
        patch("canfar.cli.login.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", return_value=credential),
        patch("canfar.server._validate_server", return_value=validated),
        patch(
            "canfar.cli.login.discover",
            side_effect=lambda idp, *, config, **_kwargs: (
                _merge_servers(
                    config,
                    discovered,
                    idp,
                )
                or discovered
            ),
        ),
    ):
        result = runner.invoke(cli, ["login", "cadc"])

    assert result.exit_code == 0
    assert "already exists" not in result.stdout


def test_auth_login_alias_delegates_to_login_flow(tmp_path: Path) -> None:
    """``canfar auth login`` remains a compatibility alias."""
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(
        idp="cadc",
        path=Path("/new/cert.pem"),
        expiry=123.0,
    )
    discovered = [
        Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri=AnyUrl(_CADC_URI),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]
    validated = discovered[0].model_copy(deep=True)

    with (
        _patch_config(config_path),
        patch("canfar.cli.login.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", return_value=credential),
        patch("canfar.server._validate_server", return_value=validated),
        patch(
            "canfar.cli.login.discover",
            side_effect=lambda idp, *, config, **_kwargs: (
                _merge_servers(
                    config,
                    discovered,
                    idp,
                )
                or discovered
            ),
        ),
    ):
        result = runner.invoke(cli, ["auth", "login", "cadc", "--force"])

    assert result.exit_code == 0
    assert "canfar auth login will be removed soon" in result.stderr
    assert "canfar login" in result.stderr
    with (
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        saved = Configuration()
    assert saved.active.authentication == "cadc"
    assert saved.active.server == "CADC-CANFAR"


def test_login_saves_auth_and_server_atomically(tmp_path: Path) -> None:
    """Login persists active Authentication and Server in one save."""
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(
        idp="cadc",
        path=Path("/new/cert.pem"),
        expiry=456.0,
    )
    discovered = [
        Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri=AnyUrl(_CADC_URI),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]
    validated = discovered[0].model_copy(deep=True)

    with (
        _patch_config(config_path),
        patch("canfar.cli.login.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", return_value=credential),
        patch("canfar.server._validate_server", return_value=validated),
        patch(
            "canfar.cli.login.discover",
            side_effect=lambda idp, *, config, **_kwargs: (
                _merge_servers(
                    config,
                    discovered,
                    idp,
                )
                or discovered
            ),
        ),
    ):
        result = runner.invoke(cli, ["login", "cadc", "--force"])

    assert result.exit_code == 0
    with patch("canfar.models.config.CONFIG_PATH", config_path):
        saved = Configuration()
    assert saved.active.authentication == "cadc"
    assert saved.active.server == "CADC-CANFAR"
    assert saved.get_credential("cadc").path == Path("/new/cert.pem")


def test_login_passes_dev_and_timeout_to_http_steps(tmp_path: Path) -> None:
    """Login --dev and --timeout flow into auth, discovery, and validation."""
    config_path = tmp_path / "config.yaml"
    credential = X509Credential(
        idp="cadc",
        path=Path("/new/cert.pem"),
        expiry=456.0,
    )
    discovered = [
        Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri=AnyUrl(_CADC_URI),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            version="v1",
            auths=["x509"],
        )
    ]
    validated = discovered[0].model_copy(deep=True)
    authenticate = MagicMock(return_value=credential)
    validate = MagicMock(return_value=validated)

    def discover(
        idp: str,
        *,
        config: Configuration,
        dev: bool,
        timeout: int,
        save: bool,
    ) -> list[Server]:
        assert idp == "cadc"
        assert dev is True
        assert timeout == 9
        assert save is False
        _merge_servers(config, discovered, idp)
        return discovered

    with (
        _patch_config(config_path),
        patch("canfar.cli.login.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
        patch("canfar.cli.login.authenticate_for_cli", authenticate),
        patch("canfar.server._validate_server", validate),
        patch("canfar.cli.login.discover", side_effect=discover),
    ):
        result = runner.invoke(
            cli,
            ["login", "cadc", "--force", "--dev", "--timeout", "9"],
        )

    assert result.exit_code == 0
    authenticate.assert_called_once()
    assert authenticate.call_args.kwargs["timeout"] == 9
    validate.assert_called_once()
    validated = validate.call_args.args[0]
    assert str(validated.uri) == _CADC_URI
    assert validate.call_args.kwargs["idp"] == "cadc"
    assert validate.call_args.kwargs["timeout"] == 9
    assert isinstance(validate.call_args.kwargs["config"], Configuration)


def test_auth_login_alias_passes_dev_and_timeout_to_login_flow() -> None:
    """Compatibility alias keeps the same discovery options as canfar login."""
    with patch("canfar.cli.login._login_flow") as login_flow:
        result = runner.invoke(
            cli,
            ["auth", "login", "cadc", "--dev", "--timeout", "7"],
        )

    assert result.exit_code == 0
    login_flow.assert_called_once_with("cadc", force=False, dev=True, timeout=7)


def test_login_existing_without_force_exits_nonzero(tmp_path: Path) -> None:
    """Repeated login without --force is rejected."""
    config_path = tmp_path / "config.yaml"
    _write_config(
        config_path,
        {
            "version": 1,
            "active": {"authentication": "cadc", "server": "CADC-CANFAR"},
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/existing/cert.pem",
                    "expiry": 1.0,
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
        },
    )

    with (
        _patch_config(config_path),
        patch("canfar.cli.login.CONFIG_PATH", config_path),
        patch("canfar.models.config.CONFIG_PATH", config_path),
    ):
        result = runner.invoke(cli, ["login", "cadc"])

    assert result.exit_code == 1
    assert "already exists" in result.stderr
