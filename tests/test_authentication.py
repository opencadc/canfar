"""Behavior tests for the public Authentication seam."""

from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl

import canfar
from canfar.authentication import AuthMode


def _write_config(path: Path, data: dict) -> None:
    path.write_text(yaml.dump(data), encoding="utf-8")


def _patch_config(path: Path):
    return patch("canfar.models.config.CONFIG_PATH", path)


def _merge_servers(
    config: canfar.models.config.Configuration,
    discovered: list,
) -> None:
    for server in discovered:
        if server.name is not None:
            config.servers[server.name] = server


class TestAuthenticationList:
    """Tests for authentication.list()."""

    def test_list_returns_saved_authentication_summaries(self, tmp_path: Path) -> None:
        """Saved authentication records are exposed as summaries."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "CADC-CANFAR",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1234567890.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            },
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            summaries = canfar.authentication.list()

        assert len(summaries) == 2
        assert all(
            isinstance(item, canfar.authentication.Authentication) for item in summaries
        )

        by_idp = {summary.idp: summary for summary in summaries}
        assert by_idp["cadc"].name == "Canadian Astronomy Data Centre"
        assert by_idp["cadc"].mode == "x509"
        assert by_idp["cadc"].expiry == 1234567890.0
        assert by_idp["cadc"].active is True
        assert by_idp["cadc"].server == "CADC-CANFAR"
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
                "server": "CADC-CANFAR",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 999.0,
                }
            },
            "servers": {
                "CADC-CANFAR": {
                    "idp": "cadc",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            },
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            summary = canfar.authentication.show()

        assert summary.idp == "cadc"
        assert summary.name == "Canadian Astronomy Data Centre"
        assert summary.mode == "x509"
        assert summary.expiry == 999.0
        assert summary.active is True
        assert summary.server == "CADC-CANFAR"


class TestAuthenticationUse:
    """Tests for authentication.use()."""

    def test_use_switches_active_authentication(self, tmp_path: Path) -> None:
        """use() selects the requested IDP as active authentication."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "CADC-CANFAR",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                },
                "SRCNet": {
                    "idp": "srcnet",
                    "uri": "ivo://srcnet.example/skaha",
                    "url": "https://srcnet.example/skaha",
                    "version": "v1",
                    "auths": ["oidc"],
                },
            },
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            canfar.authentication.use("srcnet")
            config = canfar.models.config.Configuration()

        assert config.active.authentication == "srcnet"

    def test_use_clears_incompatible_active_server(self, tmp_path: Path) -> None:
        """use() clears active server when it belongs to another IDP."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "CADC-CANFAR",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                },
                "SRCNet": {
                    "idp": "srcnet",
                    "uri": "ivo://srcnet.example/skaha",
                    "url": "https://srcnet.example/skaha",
                    "version": "v1",
                    "auths": ["oidc"],
                },
            },
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            canfar.authentication.use("srcnet")
            config = canfar.models.config.Configuration()

        assert config.active.authentication == "srcnet"
        assert config.active.server is None

    def test_import_canfar_with_null_active_server(self, tmp_path: Path) -> None:
        """Importing canfar stays safe when active server selection is cleared."""
        home = tmp_path / "home"
        config_dir = home / ".canfar"
        config_dir.mkdir(parents=True)
        config_data = {
            "version": 1,
            "active": {"authentication": "srcnet", "server": None},
            "authentication": {
                "srcnet": {
                    "mode": "oidc",
                    "endpoints": {},
                    "client": {},
                    "token": {},
                    "expiry": {},
                }
            },
            "servers": {
                "SRCNet": {
                    "idp": "srcnet",
                    "uri": "ivo://srcnet.example/skaha",
                    "url": "https://srcnet.example/skaha",
                    "version": "v1",
                    "auths": ["oidc"],
                }
            },
        }
        (config_dir / "config.yaml").write_text(
            yaml.dump(config_data), encoding="utf-8"
        )

        result = subprocess.run(
            [sys.executable, "-c", "import canfar; print('ok')"],
            env={**os.environ, "HOME": str(home)},
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "ok"

    def test_use_keeps_compatible_active_server(self, tmp_path: Path) -> None:
        """use() preserves active server when it matches the selected IDP."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "srcnet",
                "server": "SRCNet",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/saved/cadc.pem",
                    "expiry": 1.0,
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
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                },
                "SRCNet": {
                    "idp": "srcnet",
                    "uri": "ivo://srcnet.example/skaha",
                    "url": "https://srcnet.example/skaha",
                    "version": "v1",
                    "auths": ["oidc"],
                },
            },
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with _patch_config(config_path):
            canfar.authentication.use("srcnet")
            config = canfar.models.config.Configuration()

        assert config.active.authentication == "srcnet"
        assert config.active.server == "SRCNet"

    def test_use_unknown_idp_raises_key_error(self) -> None:
        """Unknown IDP keys are rejected by the built-in catalog."""
        with pytest.raises(KeyError, match="Unknown IDP"):
            canfar.authentication.use("unknown")

    def test_use_unconfigured_idp_raises_authentication_required(
        self, tmp_path: Path
    ) -> None:
        """use() fails when no saved authentication exists for the IDP."""
        config_path = tmp_path / "config.yaml"
        with (
            _patch_config(config_path),
            pytest.raises(canfar.authentication.AuthenticationError) as exc_info,
        ):
            canfar.authentication.use("srcnet")

        assert (
            exc_info.value.error.code == canfar.errors.ErrorCode.AUTHENTICATION_REQUIRED
        )


class TestAuthenticationLogin:
    """Tests for authentication.login()."""

    def test_login_unknown_idp_raises_key_error(self) -> None:
        """Unknown IDP keys are rejected by the built-in catalog."""
        with pytest.raises(KeyError, match="Unknown IDP"):
            canfar.authentication.login("unknown")

    def test_login_existing_without_force_is_noop(self, tmp_path: Path) -> None:
        """Existing authentication is preserved when force is false."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "CADC-CANFAR",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/existing/cert.pem",
                    "expiry": 42.0,
                }
            },
            "servers": {
                "CADC-CANFAR": {
                    "idp": "cadc",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            },
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)

        with (
            _patch_config(config_path),
            patch("canfar.authentication._authenticate") as mock_auth,
            patch("canfar.authentication.server_service.discover") as mock_discover,
        ):
            canfar.authentication.login("cadc")

        mock_auth.assert_not_called()
        mock_discover.assert_not_called()
        with _patch_config(config_path):
            config = canfar.models.config.Configuration()
        assert config.authentication["cadc"].path == Path("/existing/cert.pem")

    def test_login_saves_auth_and_servers_without_changing_active(
        self, tmp_path: Path
    ) -> None:
        """login() persists authentication and servers but not active selection."""
        config_path = tmp_path / "config.yaml"
        credential = canfar.models.auth.X509Credential(
            idp="cadc",
            path=Path("/new/cert.pem"),
            expiry=777.0,
        )
        discovered = [
            canfar.models.http.Server(
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
                "canfar.authentication.server_service.discover",
                side_effect=lambda _idp, *, config, **_kwargs: (
                    _merge_servers(
                        config,
                        discovered,
                    )
                    or discovered
                ),
            ),
        ):
            canfar.authentication.login("cadc", force=True)

        with _patch_config(config_path):
            config = canfar.models.config.Configuration()

        assert config.active.authentication == "cadc"
        assert config.active.server == "canfar"
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
                "server": "CADC-CANFAR",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/old/cert.pem",
                    "expiry": 1.0,
                }
            },
            "servers": {
                "CADC-CANFAR": {
                    "idp": "cadc",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                }
            },
        }
        config_path = tmp_path / "config.yaml"
        _write_config(config_path, config_data)
        credential = canfar.models.auth.X509Credential(
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
                "canfar.authentication.server_service.discover",
                return_value=[],
            ),
        ):
            canfar.authentication.login("cadc", force=True)

        with _patch_config(config_path):
            config = canfar.models.config.Configuration()

        assert config.get_credential("cadc").path == Path("/new/cert.pem")
        assert config.get_credential("cadc").expiry == 888.0


class TestAuthenticationModuleExports:
    """Tests for package-level Authentication seam exports."""

    def test_canfar_exports_authentication_module(self) -> None:
        """canfar.authentication is importable from the package root."""
        assert canfar.authentication is importlib.import_module("canfar.authentication")
        assert callable(canfar.authentication.login)
        assert callable(canfar.authentication.use)
        assert callable(canfar.authentication.list)
        assert callable(canfar.authentication.show)

    def test_canfar_exports_login_helper(self) -> None:
        """canfar.login aliases authentication.login."""
        assert canfar.login is canfar.authentication.login

    def test_authentication_re_exports_auth_mode(self) -> None:
        """AuthMode remains importable from the public authentication module."""
        assert "AuthMode" in canfar.authentication.__all__
        assert AuthMode.__args__ == ("x509", "oidc")

    def test_canfar_exports_config_paths(self) -> None:
        """Configuration paths are explicit package-root exports."""
        assert "CONFIG_DIR" in canfar.__all__
        assert "CONFIG_PATH" in canfar.__all__
