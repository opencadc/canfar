"""Focused behavior tests for config v1 and legacy migration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from canfar.config.migration import (
    ConfigMigrationError,
    backup_path,
    migrate_legacy_config,
)
from canfar.models.config import Configuration


class TestConfigV1Defaults:
    """Test default v1 configuration shape."""

    def test_default_v1_shape_has_cadc_placeholder(self, tmp_path: Path) -> None:
        """Fresh config uses version 1 with default CADC authentication and server."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 1
        assert config.active.authentication == "cadc"
        assert str(config.active.server) == "ivo://cadc.nrc.ca/skaha"

        assert len(config.authentication) == 1
        cred = config.authentication[0]
        assert cred.idp == "cadc"
        assert cred.mode == "x509"
        assert cred.path == Path.home() / ".ssl" / "cadcproxy.pem"

        assert len(config.server) == 1
        srv = config.server[0]
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
        """V1 authentication records are decoupled from server selection."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        cred = config.authentication[0]
        assert not hasattr(cred, "server") or "server" not in cred.model_fields


class TestConfigV1EnvOverrides:
    """Test nested active environment variable overrides."""

    def test_active_env_overrides_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CANFAR_ACTIVE__AUTHENTICATION and CANFAR_ACTIVE__SERVER override YAML."""
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
                    "path": "/yaml/cert.pem",
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
        config_path.write_text(yaml.dump(config_data), encoding="utf-8")

        monkeypatch.setenv("CANFAR_ACTIVE__AUTHENTICATION", "srcnet")
        monkeypatch.setenv("CANFAR_ACTIVE__SERVER", "ivo://srcnet.example/skaha")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.active.authentication == "srcnet"
        assert str(config.active.server) == "ivo://srcnet.example/skaha"


class TestConfigV1LegacyMigration:
    """Test legacy configuration backup and reset behavior."""

    def test_legacy_config_is_backed_up_and_reset_to_v1_defaults(
        self, tmp_path: Path
    ) -> None:
        """Missing version triggers backup and default v1 rewrite."""
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

        fixed_time = 1_700_000_000.0
        clock = lambda: fixed_time  # noqa: E731

        assert migrate_legacy_config(config_path, clock=clock) is True

        backup = backup_path(config_path, clock)
        assert backup.exists()
        assert backup.read_text(encoding="utf-8") == yaml.dump(legacy)

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 1
        assert config.active.authentication == "cadc"
        assert config.authentication[0].path == Path.home() / ".ssl" / "cadcproxy.pem"

    def test_legacy_migration_preserves_registry_and_console(
        self, tmp_path: Path
    ) -> None:
        """Registry and console sections survive legacy reset."""
        legacy = {
            "active": "default",
            "contexts": {"default": {"mode": "x509", "expiry": 0.0}},
            "registry": {
                "url": "https://registry.example.com",
                "username": "legacy-user",
                "secret": "legacy-secret",
            },
            "console": {"width": 80},
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(legacy), encoding="utf-8")

        migrate_legacy_config(config_path, clock=lambda: 1_700_000_000.0)

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.registry.username == "legacy-user"
        assert str(config.registry.url).rstrip("/") == "https://registry.example.com"
        assert config.console.width == 80

    def test_backup_failure_leaves_original_untouched(self, tmp_path: Path) -> None:
        """Failed backup raises config.invalid and does not rewrite config."""
        legacy = {"active": "default", "contexts": {}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(legacy), encoding="utf-8")
        original = config_path.read_text(encoding="utf-8")

        copy_patch = patch(
            "canfar.config.migration.shutil.copy2",
            side_effect=OSError("denied"),
        )
        with copy_patch, pytest.raises(ConfigMigrationError) as exc_info:
            migrate_legacy_config(config_path, clock=lambda: 1_700_000_000.0)

        assert exc_info.value.code == "config.invalid"
        assert config_path.read_text(encoding="utf-8") == original

    def test_existing_backup_is_not_overwritten(self, tmp_path: Path) -> None:
        """Migration uses a new backup name when the first candidate exists."""
        legacy = {"active": "default", "contexts": {}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(legacy), encoding="utf-8")

        clock = lambda: 1_700_000_000.0  # noqa: E731
        first_backup = backup_path(config_path, clock)
        first_backup.write_text("existing backup", encoding="utf-8")

        migrate_legacy_config(config_path, clock=clock)

        assert first_backup.read_text(encoding="utf-8") == "existing backup"
        suffix_backups = list(tmp_path.glob("config.yaml.*.back*"))
        assert len(suffix_backups) >= 2

    def test_unsupported_version_triggers_migration(self, tmp_path: Path) -> None:
        """Configs with unsupported version values are treated as legacy."""
        legacy = {"version": 99, "active": {"authentication": "cadc", "server": "x"}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(legacy), encoding="utf-8")

        assert migrate_legacy_config(config_path, clock=lambda: 1_700_000_000.0) is True

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 1
        assert config.active.authentication == "cadc"

    def test_v1_config_loads_without_migration(self, tmp_path: Path) -> None:
        """Valid v1 files load unchanged and create no backup."""
        v1 = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/saved/cert.pem",
                    "expiry": 9.0,
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
            ],
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(v1), encoding="utf-8")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.authentication[0].path == Path("/saved/cert.pem")
        assert list(tmp_path.glob("*.back")) == []

    def test_legacy_canfar_active_env_is_not_used(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Legacy CANFAR_ACTIVE env var does not override v1 active selection."""
        v1 = {
            "version": 1,
            "active": {
                "authentication": "cadc",
                "server": "ivo://cadc.nrc.ca/skaha",
            },
            "authentication": [
                {
                    "idp": "cadc",
                    "mode": "x509",
                    "path": "/saved/cert.pem",
                    "expiry": 9.0,
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
            ],
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(v1), encoding="utf-8")
        monkeypatch.setenv("CANFAR_ACTIVE", "legacy-context-name")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.active.authentication == "cadc"
