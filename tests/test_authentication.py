"""Behavior tests for the public Authentication seam."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl

import canfar
from canfar import authentication as canfar_authentication
from canfar.authentication import (
    Authentication,
    AuthenticationError,
    login,
    show,
    use,
)
from canfar.authentication import (
    list as auth_list,
)
from canfar.errors import ErrorCode
from canfar.models.auth import X509Credential
from canfar.models.config import Configuration
from canfar.models.http import Server


def _write_config(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data), encoding="utf-8")


def _patch_config(path: Path):
    return patch("canfar.models.config.CONFIG_PATH", path)


class TestAuthenticationList:
    """Tests for authentication.list()."""

    def test_list_returns_saved_authentication_summaries(self, tmp_path: Path) -> None:
        """Saved authentication records are exposed as summaries."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1234567890.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            ],
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            summaries = auth_list()

        assert len(summaries) == 2
        assert all(isinstance(item, Authentication) for item in summaries)

        by_idp = {summary.idp: summary for summary in summaries}
        assert by_idp["cadc"].name == "Canadian Astronomy Data Centre"
        assert by_idp["cadc"].mode == "x509"
        assert by_idp["cadc"].expiry == 1234567890.0
        assert by_idp["cadc"].active is True
        assert by_idp["cadc"].server == "ivo://cadc.nrc.ca/skaha"
        assert by_idp["srcnet"].active is False
        assert by_idp["srcnet"].server is None


class TestAuthenticationShow:
    """Tests for authentication.show()."""

    def test_show_returns_active_authentication_summary(self, tmp_path: Path) -> None:
        """Active authentication is summarized with server reference when set."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 999.0,
                }
            ],
            "server": [
                {
                    "idp": "cadc",
                    "name": "CADC-CANFAR",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            ],
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            summary = show()

        assert summary.idp == "cadc"
        assert summary.name == "Canadian Astronomy Data Centre"
        assert summary.mode == "x509"
        assert summary.expiry == 999.0
        assert summary.active is True
        assert summary.server == "ivo://cadc.nrc.ca/skaha"


class TestAuthenticationUse:
    """Tests for authentication.use()."""

    def test_use_switches_active_authentication(self, tmp_path: Path) -> None:
        """use() selects the requested IDP as active authentication."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
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
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            use("srcnet")
            config = Configuration()

        assert config.active.authentication == "srcnet"

    def test_use_clears_incompatible_active_server(self, tmp_path: Path) -> None:
        """use() clears active server when it belongs to another IDP."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
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
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            use("srcnet")
            config = Configuration()

        assert config.active.authentication == "srcnet"
        assert config.active.server is None

    def test_use_keeps_compatible_active_server(self, tmp_path: Path) -> None:
        """use() preserves active server when it matches the selected IDP."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "srcnet",
                "server": "ivo://srcnet.example/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
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
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            use("srcnet")
            config = Configuration()

        assert config.active.authentication == "srcnet"
        assert str(config.active.server) == "ivo://srcnet.example/skaha"

    def test_use_unknown_idp_raises_key_error(self) -> None:
        """Unknown IDP keys are rejected by the built-in catalog."""
        with pytest.raises(KeyError, match="Unknown IDP"):
            use("unknown")

    def test_use_unconfigured_idp_raises_authentication_required(
        self, tmp_path: Path
    ) -> None:
        """use() fails when no saved authentication exists for the IDP."""
        config_path = tmp_path / "config.yaml"
        with (
            _patch_config(config_path),
            pytest.raises(AuthenticationError) as exc_info,
        ):
            use("srcnet")

        assert exc_info.value.error.code == ErrorCode.AUTHENTICATION_REQUIRED


class TestAuthenticationLogin:
    """Tests for authentication.login()."""

    def test_login_unknown_idp_raises_key_error(self) -> None:
        """Unknown IDP keys are rejected by the built-in catalog."""
        with pytest.raises(KeyError, match="Unknown IDP"):
            login("unknown")

    def test_login_existing_without_force_is_noop(self, tmp_path: Path) -> None:
        """Existing authentication is preserved when force is false."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/existing/cert.pem",
                    "expiry": 42.0,
                }
            ],
            "server": [
                {
                    "idp": "cadc",
                    "name": "CADC-CANFAR",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            ],
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with (
            _patch_config(config_path),
            patch("canfar.authentication._authenticate") as mock_auth,
            patch(
                "canfar.authentication._discover_servers",
                new=AsyncMock(return_value=[]),
            ),
        ):
            login("cadc")

        mock_auth.assert_not_called()
        with _patch_config(config_path):
            config = Configuration()
        assert config.authentication[0].path == Path("/existing/cert.pem")

    def test_login_saves_auth_and_servers_without_changing_active(
        self, tmp_path: Path
    ) -> None:
        """login() persists authentication and servers but not active selection."""
        config_path = tmp_path / "config.yaml"
        credential = X509Credential(
            idp="cadc",
            path=Path("/new/cert.pem"),
            expiry=777.0,
        )
        discovered = [
            Server(
                idp="cadc",
                name="CADC-CANFAR",
                uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
                url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
            )
        ]

        with (
            _patch_config(config_path),
            patch(
                "canfar.authentication._authenticate",
                return_value=credential,
            ),
            patch(
                "canfar.authentication._discover_servers",
                new=AsyncMock(return_value=discovered),
            ),
        ):
            login("cadc", force=True)

        with _patch_config(config_path):
            config = Configuration()

        assert config.active.authentication == "cadc"
        assert str(config.active.server) == "ivo://cadc.nrc.ca/skaha"
        assert config.get_credential("cadc").path == Path("/new/cert.pem")
        assert str(config.get_server_by_uri("ivo://cadc.nrc.ca/skaha").url) == (
            "https://ws-uv.canfar.net/skaha"
        )

    def test_login_with_force_replaces_existing_credential(
        self, tmp_path: Path
    ) -> None:
        """force=True overwrites an existing authentication record."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/old/cert.pem",
                    "expiry": 1.0,
                }
            ],
            "server": [
                {
                    "idp": "cadc",
                    "name": "CADC-CANFAR",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            ],
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)
        credential = X509Credential(
            idp="cadc",
            path=Path("/new/cert.pem"),
            expiry=888.0,
        )

        with (
            _patch_config(config_path),
            patch(
                "canfar.authentication._authenticate",
                return_value=credential,
            ),
            patch(
                "canfar.authentication._discover_servers",
                new=AsyncMock(return_value=[]),
            ),
        ):
            login("cadc", force=True)

        with _patch_config(config_path):
            config = Configuration()

        assert config.get_credential("cadc").path == Path("/new/cert.pem")
        assert config.get_credential("cadc").expiry == 888.0


class TestAuthenticationModuleExports:
    """Tests for package-level Authentication seam exports."""

    def test_canfar_exports_authentication_module(self) -> None:
        """canfar.authentication is importable from the package root."""
        assert canfar.authentication is canfar_authentication
        assert callable(canfar_authentication.login)
        assert callable(canfar_authentication.use)
        assert callable(canfar_authentication.list)
        assert callable(canfar_authentication.show)

    def test_canfar_exports_login_helper(self) -> None:
        """canfar.login aliases authentication.login."""
        assert canfar.login is canfar_authentication.login
