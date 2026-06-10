"""Focused behavior tests for persisted CANFAR configuration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from canfar.config.editor import set_value as set_config_value
from canfar.config.migration import (
    ConfigResetRequiredError,
    ensure_current_config,
)
from canfar.config.selection import set_active_selection as select_active_server
from canfar.config.store import save_config
from canfar.models.config import Configuration
from canfar.models.http import Server


class TestConfigDefaults:
    """Test default configuration shape."""

    def test_default_shape_has_cadc_placeholder(self, tmp_path: Path) -> None:
        """Fresh config uses the default CADC authentication and server."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 1
        assert config.active.authentication == "cadc"
        assert config.active.server == "canfar"

        assert set(config.authentication) == {"cadc"}
        cred = config.authentication["cadc"]
        assert cred.idp == "cadc"
        assert cred.mode == "x509"
        assert cred.path == Path.home() / ".ssl" / "cadcproxy.pem"

        assert set(config.servers) == {"canfar"}
        srv = config.servers["canfar"]
        assert srv.idp == "cadc"
        assert srv.name == "canfar"
        assert str(srv.uri) == "ivo://cadc.nrc.ca/skaha"
        assert str(srv.url) == "https://ws-uv.canfar.net/skaha"
        assert srv.version == "v1"
        assert srv.auths == ["x509"]
        assert srv.cores == 2
        assert srv.ram == 16
        assert srv.gpus == 0
        assert config.registry.model_dump(exclude_none=True) == {}
        assert config.console.width == 120

    def test_authentication_credentials_have_no_embedded_server(
        self, tmp_path: Path
    ) -> None:
        """Authentication records are decoupled from server selection."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        cred = config.authentication["cadc"]
        assert not hasattr(cred, "server") or "server" not in cred.model_fields


class TestConfigEnvOverrides:
    """Test nested active environment variable overrides."""

    def test_active_env_overrides_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CANFAR_ACTIVE__AUTHENTICATION and CANFAR_ACTIVE__SERVER override YAML."""
        config_data = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "canfar",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/yaml/cert.pem",
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
                "canfar": {
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
        config_path.write_text(yaml.dump(config_data), encoding="utf-8")

        monkeypatch.setenv("CANFAR_ACTIVE__AUTHENTICATION", "srcnet")
        monkeypatch.setenv("CANFAR_ACTIVE__SERVER", "SRCNet")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.active.authentication == "srcnet"
        assert config.active.server == "SRCNet"


class TestConfigServersPaths:
    """Test dotted-path access to name-keyed servers."""

    def test_get_and_set_servers_canfar_url(self, tmp_path: Path) -> None:
        """servers.<name>.<field> paths round-trip through get_value/set_value."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert str(config.get_value("servers.canfar.url")) == (
            "https://ws-uv.canfar.net/skaha"
        )

        updated = config.set_value(
            "servers.canfar.url",
            "https://example.test/skaha",
        )
        assert str(updated.get_value("servers.canfar.url")) == (
            "https://example.test/skaha"
        )


class TestConfigServices:
    """Test configuration storage and action helpers."""

    def test_editor_and_store_update_config_without_model_io(
        self,
        tmp_path: Path,
    ) -> None:
        """Config editing and persistence live outside the Pydantic model."""
        config_path = tmp_path / "config.yaml"
        config = Configuration()

        updated = set_config_value(config, "console.width", 132)
        save_config(updated, config_path)

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            loaded = Configuration()

        assert loaded.console.width == 132

    def test_selection_service_sets_active_server(self) -> None:
        """Active server selection is provided as a config action helper."""
        config = Configuration()
        server = Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri="ivo://cadc.example/skaha",
            url="https://cadc.example/skaha",
            version="v1",
            auths=["x509"],
        )

        select_active_server(config, "cadc", server)

        assert config.active.server == "CADC-CANFAR"
        assert config.get_server_by_uri("ivo://cadc.example/skaha").name == (
            "CADC-CANFAR"
        )


class TestConfigManualReset:
    """Test legacy configuration reset-required behavior."""

    def test_legacy_config_requires_manual_reset_without_backup(
        self, tmp_path: Path
    ) -> None:
        """Missing version raises reset-needed without rewriting config."""
        legacy = {
            "active": "default",
            "contexts": {
                "default": {
                    "mode": "x509",
                    "path": "/legacy/cert.pem",
                    "expiry": 111.0,
                },
            },
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(legacy), encoding="utf-8")
        original = config_path.read_text(encoding="utf-8")

        with pytest.raises(ConfigResetRequiredError) as exc_info:
            ensure_current_config(config_path)

        assert exc_info.value.code == "config.invalid"
        assert str(exc_info.value) == (
            "CANFAR configuration reset needed. "
            f"Run `rm -rf {config_path}` and perform a new login"
        )
        assert config_path.read_text(encoding="utf-8") == original
        assert list(tmp_path.glob("*.back*")) == []

    def test_unsupported_version_requires_reset(self, tmp_path: Path) -> None:
        """Unsupported version requires manual reset."""
        legacy = {"version": 99, "active": {"authentication": "cadc", "server": "x"}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(legacy), encoding="utf-8")

        with pytest.raises(ConfigResetRequiredError):
            ensure_current_config(config_path)

    def test_current_config_loads_without_reset(self, tmp_path: Path) -> None:
        """Valid current config files load unchanged and create no backup."""
        current = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "canfar",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/saved/cert.pem",
                    "expiry": 9.0,
                },
            },
            "servers": {
                "canfar": {
                    "idp": "cadc",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                },
            },
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(current), encoding="utf-8")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.authentication["cadc"].path == Path("/saved/cert.pem")
        assert list(tmp_path.glob("*.back")) == []

    def test_legacy_canfar_active_env_is_not_used(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Legacy CANFAR_ACTIVE env var does not override active selection."""
        current = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "canfar",
            },
            "authentication": {
                "cadc": {
                    "mode": "x509",
                    "path": "/saved/cert.pem",
                    "expiry": 9.0,
                },
            },
            "servers": {
                "canfar": {
                    "idp": "cadc",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                    "version": "v1",
                    "auths": ["x509"],
                },
            },
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(current), encoding="utf-8")
        monkeypatch.setenv("CANFAR_ACTIVE", "legacy-context-name")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.active.authentication == "cadc"
