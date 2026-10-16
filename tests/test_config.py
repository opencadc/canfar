"""Focused behavior tests for persisted CANFAR configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

import canfar.authentication as authentication_service
from canfar.config.migration import UPGRADES, ConfigResetRequiredError, upgrade
from canfar.models.auth import X509Credential
from canfar.models.config import Configuration
from canfar.models.http import Server


class TestConfigDefaults:
    """Test default configuration shape."""

    def test_default_shape_has_cadc_placeholder(self, tmp_path: Path) -> None:
        """Fresh config uses the default CADC authentication and server."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 2
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
        assert srv.resources is None
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
            "version": 2,
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
        """servers.<name>.<field> paths round-trip through the editor."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert str(config.editor.get("servers.canfar.url")) == (
            "https://ws-uv.canfar.net/skaha"
        )

        config.editor.set(
            "servers.canfar.url",
            "https://example.test/skaha",
        )
        assert str(config.editor.get("servers.canfar.url")) == (
            "https://example.test/skaha"
        )


class TestConfigEditing:
    """Test validated configuration edits and domain-owned persistence."""

    def test_invalid_server_selection_preserves_configuration(
        self,
        tmp_path: Path,
    ) -> None:
        """An invalid server mapping changes neither memory nor persisted YAML."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.editor.save()
            persisted = config_path.read_bytes()

            invalid = Server(
                idp="cadc",
                name="invalid.name",
                uri="ivo://invalid.example/skaha",
                url="https://invalid.example/skaha",
                version="v1",
                auths=["x509"],
            )
            with pytest.raises(ValidationError, match="Invalid server name"):
                config.editor.set("servers", {"invalid.name": invalid})

        assert config.active.server == "canfar"
        assert set(config.servers) == {"canfar"}
        assert config_path.read_bytes() == persisted

    def test_editor_credential_update_preserves_other_authentication_records(
        self,
        tmp_path: Path,
    ) -> None:
        """Adding an Authentication Record preserves and persists existing records."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            cadc_path = config.authentication["cadc"].path
            config.editor.set(
                "authentication.srcnet",
                X509Credential(
                    idp="srcnet",
                    path=Path("/srcnet/cert.pem"),
                    expiry=42.0,
                ),
            )
            config.editor.save()
            loaded = Configuration()

        assert set(loaded.authentication) == {"cadc", "srcnet"}
        assert loaded.authentication["cadc"].path == cadc_path
        assert loaded.authentication["srcnet"].path == Path("/srcnet/cert.pem")

    def test_update_known_credential_preserves_unrelated_state(
        self,
        tmp_path: Path,
    ) -> None:
        """Updating a known Authentication Record changes only that record."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.editor.set(
                "authentication.srcnet",
                X509Credential(
                    idp="srcnet",
                    path=Path("/srcnet/cert.pem"),
                    expiry=42.0,
                ),
            )
            active = config.active.model_dump(mode="python")
            servers = config.servers

            config.editor.set(
                "authentication.cadc",
                X509Credential(
                    idp="cadc",
                    path=Path("/updated/cadc.pem"),
                    expiry=84.0,
                ),
            )
            config.editor.save()
            loaded = Configuration()

        assert loaded.authentication["cadc"].path == Path("/updated/cadc.pem")
        assert loaded.authentication["srcnet"].path == Path("/srcnet/cert.pem")
        assert loaded.active.model_dump(mode="python") == active
        assert loaded.servers == servers

    def test_upsert_server_preserves_other_science_platform_servers(
        self,
        tmp_path: Path,
    ) -> None:
        """Adding a Science Platform Server preserves existing Server Names."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.editor.set(
                "servers.SRCNet",
                Server(
                    idp="srcnet",
                    name="SRCNet",
                    uri="ivo://srcnet.example/skaha",
                    url="https://srcnet.example/skaha",
                    version="v1",
                    auths=["oidc"],
                ),
            )
            config.editor.save()
            loaded = Configuration()

        assert set(loaded.servers) == {"canfar", "SRCNet"}
        assert str(loaded.servers["canfar"].uri) == "ivo://cadc.nrc.ca/skaha"
        assert str(loaded.servers["SRCNet"].uri) == "ivo://srcnet.example/skaha"

    def test_remove_authentication_preserves_unrelated_records(
        self,
        tmp_path: Path,
    ) -> None:
        """Removing one Authentication also removes only its associated Servers."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.editor.set(
                "authentication.srcnet",
                X509Credential(
                    idp="srcnet",
                    path=Path("/srcnet/cert.pem"),
                    expiry=42.0,
                ),
            )
            config.editor.set(
                "servers.SRCNet",
                Server(
                    idp="srcnet",
                    name="SRCNet",
                    uri="ivo://srcnet.example/skaha",
                    url="https://srcnet.example/skaha",
                    version="v1",
                    auths=["oidc"],
                ),
            )
            config.editor.set(
                "active",
                config.active.model_copy(
                    update={
                        "authentication": "srcnet",
                        "server": "SRCNet",
                        "servers": {"srcnet": "SRCNet"},
                    }
                ),
            )
            config.editor.save()
            authentication_service.remove("cadc", force=True)
            loaded = Configuration()

        assert set(loaded.authentication) == {"srcnet"}
        assert set(loaded.servers) == {"SRCNet"}
        assert loaded.active.authentication == "srcnet"
        assert loaded.active.server == "SRCNet"

    def test_editor_updates_config_without_model_io(
        self,
        tmp_path: Path,
    ) -> None:
        """Config editing and persistence live outside the Pydantic model."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.editor.set("console.width", 132)
            config.editor.save()
            loaded = Configuration()

        assert loaded.console.width == 132

    def test_editor_sets_active_server(self) -> None:
        """Active server selection remains ordinary validated data."""
        config = Configuration()
        server = Server(
            idp="cadc",
            name="CADC-CANFAR",
            uri="ivo://cadc.example/skaha",
            url="https://cadc.example/skaha",
            version="v1",
            auths=["x509"],
        )

        config.editor.set("servers.CADC-CANFAR", server)
        config.editor.set(
            "active",
            config.active.model_copy(
                update={
                    "server": "CADC-CANFAR",
                    "servers": {"cadc": "CADC-CANFAR"},
                }
            ),
        )

        assert config.active.server == "CADC-CANFAR"
        assert config.servers["CADC-CANFAR"].name == ("CADC-CANFAR")


class TestRetiredServerFields:
    """Test configuration files written before Server resources existed."""

    def test_v1_4_1_server_limits_load_and_are_dropped_on_save(
        self, tmp_path: Path
    ) -> None:
        """Flat v1.4.1 limits are dropped on migration and stay unknown."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            yaml.dump(
                {
                    "version": 1,
                    "active": {"authentication": "cadc", "server": "canfar"},
                    "authentication": {
                        "cadc": {"mode": "x509", "path": "/c.pem", "expiry": 1.0}
                    },
                    "servers": {
                        "canfar": {
                            "idp": "cadc",
                            "uri": "ivo://cadc.nrc.ca/skaha",
                            "url": "https://ws-uv.canfar.net/skaha",
                            "version": "v1",
                            "cores": 2,
                            "ram": 16,
                            "gpus": 0,
                            "status": "reachable",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.editor.save()

        assert config.servers["canfar"].resources is None
        saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert {"cores", "ram", "gpus", "status"}.isdisjoint(saved["servers"]["canfar"])

    def test_editing_a_retired_server_field_fails(self, tmp_path: Path) -> None:
        """Edits name ``resources`` instead of silently dropping retired keys."""
        with patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"):
            config = Configuration()

            with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
                config.editor.set("servers.canfar.cores", 4)


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

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            pytest.raises(ConfigResetRequiredError) as exc_info,
        ):
            Configuration()

        assert exc_info.value.code == "config.invalid"
        assert str(exc_info.value) == (
            "CANFAR config error:\n  version = <missing> (expected 2)"
        )
        assert exc_info.value.hint == (
            "If you recently updated canfar, reset the configuration with "
            f"`rm {config_path}`, then run `canfar login` and try again."
        )
        assert config_path.read_text(encoding="utf-8") == original
        assert list(tmp_path.glob("*.back*")) == []

    def test_unsupported_version_requires_reset(self, tmp_path: Path) -> None:
        """Unsupported version requires manual reset."""
        legacy = {"version": 99, "active": {"authentication": "cadc", "server": "x"}}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(legacy), encoding="utf-8")

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            pytest.raises(ConfigResetRequiredError, match="expected 2"),
        ):
            Configuration()

    def test_current_config_loads_without_reset(self, tmp_path: Path) -> None:
        """Valid current config files load unchanged and create no backup."""
        current = {
            "version": 2,
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
        original = config_path.read_bytes()

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.authentication["cadc"].path == Path("/saved/cert.pem")
        assert config_path.read_bytes() == original
        assert list(tmp_path.glob("*.back")) == []

    def test_legacy_canfar_active_env_is_not_used(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Legacy CANFAR_ACTIVE env var does not override active selection."""
        current = {
            "version": 2,
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


class TestSchemaMigration:
    """Test rewriting a written version 1 configuration as version 2."""

    def test_every_older_version_has_an_upgrade_step(self) -> None:
        """Bumping the schema needs a step from the previous version."""
        current = Configuration.model_fields["version"].default
        assert set(UPGRADES) == set(range(1, current))

    def test_upgrade_runs_each_step_in_order(self) -> None:
        """A version 1 document passes through every step to the target."""

        def v2_to_v3(data: dict[str, Any]) -> dict[str, Any]:
            data["steps"].append(2)
            return data

        with patch.dict(UPGRADES, {2: v2_to_v3}):
            upgraded = upgrade(
                {"version": 1, "steps": [1], "servers": {"a": {"cores": 2}}},
                1,
                {"version": 3, "console": {"width": 120}},
            )

        assert upgraded == {
            "version": 3,
            "steps": [1, 2],
            "servers": {"a": {}},
            "console": {"width": 120},
        }

    def test_missing_file_uses_defaults_and_writes_nothing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No configuration file stays missing and prints no migration message."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 2
        assert not config_path.exists()
        assert capsys.readouterr().err == ""

    def test_version_1_file_is_rewritten_once(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A v1.4.1 file gains current defaults and keeps the user's settings."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
version: 1
active:
  authentication: cadc
  server: canfar
authentication:
  cadc:
    mode: x509
    path: /home/ada/.ssl/cadcproxy.pem
    expiry: 1800000000.0
servers:
  canfar:
    idp: cadc
    uri: ivo://cadc.nrc.ca/skaha
    url: https://ws-uv.canfar.net/skaha
    version: v1
    auths: [x509]
    cores: 8
    ram: 32
    gpus: 1
  sweSRC:
    idp: srcnet
    uri: ivo://swesrc.chalmers.se/skaha
    url: https://services.swesrc.chalmers.se/skaha
    version: v1
console:
  width: 100
  file: /tmp/out.txt
""".strip(),
            encoding="utf-8",
        )

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            captured = capsys.readouterr()
            rewritten = config_path.read_bytes()
            again = Configuration()

        assert captured.err == "Migrating canfar client config v1 → v2\n"
        assert capsys.readouterr().err == ""
        assert config_path.read_bytes() == rewritten
        assert again.version == 2
        saved = yaml.safe_load(rewritten)
        canfar_server = saved["servers"]["canfar"]
        assert saved["version"] == 2
        assert saved["authentication"]["cadc"]["path"] == "/home/ada/.ssl/cadcproxy.pem"
        assert saved["authentication"]["cadc"]["expiry"] == 1800000000.0
        assert saved["console"]["width"] == 100
        assert saved["console"]["banner"] is True
        assert "file" not in saved["console"]
        assert {"cores", "ram", "gpus", "status"}.isdisjoint(canfar_server)
        assert "resources" not in canfar_server
        assert canfar_server["storage"]["arc"]["url"] == "https://ws-uv.canfar.net/arc"
        assert (
            canfar_server["storage"]["vault"]["url"]
            == "https://cadc-west-01.canfar.net/vault"
        )
        assert saved["servers"]["sweSRC"]["url"] == (
            "https://services.swesrc.chalmers.se/skaha"
        )
        assert canfar_server["name"] == "canfar"
        assert saved["servers"]["sweSRC"]["name"] == "sweSRC"
        assert config.servers["canfar"].resources is None
        assert config.console.width == 100

    def test_string_version_1_migrates(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A quoted version 1 is the same schema as the integer."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "version: '1'\nactive:\n  authentication: cadc\n  server: canfar\n",
            encoding="utf-8",
        )

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 2
        assert yaml.safe_load(config_path.read_text(encoding="utf-8"))["version"] == 2
        assert capsys.readouterr().err == "Migrating canfar client config v1 → v2\n"

    def test_version_2_string_loads_without_rewrite(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A quoted version 2 is current and is not rewritten."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
version: "2"
active:
  authentication: cadc
  server: canfar
authentication:
  cadc:
    mode: x509
    path: /saved/cert.pem
    expiry: 9.0
servers:
  canfar:
    idp: cadc
    uri: ivo://cadc.nrc.ca/skaha
    url: https://ws-uv.canfar.net/skaha
    version: v1
    auths: [x509]
""".strip(),
            encoding="utf-8",
        )
        original = config_path.read_bytes()

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 2
        assert config.authentication["cadc"].path == Path("/saved/cert.pem")
        assert config_path.read_bytes() == original
        assert capsys.readouterr().err == ""

    def test_removed_default_server_is_restored(self, tmp_path: Path) -> None:
        """Omitted shipped defaults return because the new defaults are the base."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
version: 1
active:
  authentication: srcnet
  server: sweSRC
authentication:
  srcnet:
    mode: oidc
servers:
  sweSRC:
    idp: srcnet
    uri: ivo://swesrc.chalmers.se/skaha
    url: https://services.swesrc.chalmers.se/skaha
    version: v1
""".strip(),
            encoding="utf-8",
        )

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert set(config.servers) == {"canfar", "sweSRC"}
        assert set(config.authentication) == {"cadc", "srcnet"}
        assert config.active.server == "sweSRC"

    def test_saved_storage_endpoint_is_kept(self, tmp_path: Path) -> None:
        """A saved arc endpoint stays, and an omitted vault endpoint is filled."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
version: 1
active:
  authentication: cadc
  server: canfar
authentication:
  cadc:
    mode: x509
    path: /c.pem
    expiry: 1.0
servers:
  canfar:
    idp: cadc
    uri: ivo://cadc.nrc.ca/skaha
    url: https://ws-uv.canfar.net/skaha
    version: v1
    storage:
      arc:
        uri: ivo://cadc.nrc.ca/arc
        url: https://example.test/arc
""".strip(),
            encoding="utf-8",
        )

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        storage = config.servers["canfar"].storage
        assert str(storage["arc"].url) == "https://example.test/arc"
        assert str(storage["vault"].url) == "https://cadc-west-01.canfar.net/vault"

    def test_oidc_secrets_are_written_unmasked(self, tmp_path: Path) -> None:
        """OpenID Connect secrets in the rewritten file match the version 1 file."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
version: 1
active:
  authentication: cadc
  server: canfar
authentication:
  cadc:
    mode: x509
    path: /c.pem
    expiry: 1.0
  srcnet:
    mode: oidc
    client:
      secret: super-secret
    token:
      access: access-token
      refresh: refresh-token
servers:
  canfar:
    idp: cadc
    uri: ivo://cadc.nrc.ca/skaha
    url: https://ws-uv.canfar.net/skaha
    version: v1
""".strip(),
            encoding="utf-8",
        )

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        srcnet = saved["authentication"]["srcnet"]
        assert srcnet["client"]["secret"] == "super-secret"
        assert srcnet["token"]["access"] == "access-token"
        assert srcnet["token"]["refresh"] == "refresh-token"
        credential = config.authentication["srcnet"]
        assert credential.client.secret is not None
        assert credential.client.secret.get_secret_value() == "super-secret"
        assert credential.token.access is not None
        assert credential.token.access.get_secret_value() == "access-token"

    def test_environment_override_is_not_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A CANFAR_* override applies in memory and stays out of the file."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
version: 1
active:
  authentication: cadc
  server: canfar
authentication:
  cadc:
    mode: x509
    path: /c.pem
    expiry: 1.0
console:
  width: 100
servers:
  canfar:
    idp: cadc
    uri: ivo://cadc.nrc.ca/skaha
    url: https://ws-uv.canfar.net/skaha
    version: v1
""".strip(),
            encoding="utf-8",
        )
        monkeypatch.setenv("CANFAR_CONSOLE__WIDTH", "80")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.console.width == 80
        saved = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert saved["console"]["width"] == 100

    def test_invalid_version_1_is_not_written(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A version 1 file that still fails validation is left untouched."""
        config_path = tmp_path / "config.yaml"
        original = "version: 1\nfuture_key: true\n"
        config_path.write_text(original, encoding="utf-8")

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            pytest.raises(ConfigResetRequiredError, match="future_key"),
        ):
            Configuration()

        assert config_path.read_text(encoding="utf-8") == original
        assert capsys.readouterr().err == ""

    def test_invalid_yaml_is_not_written(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Malformed YAML raises the reset error and is not rewritten."""
        config_path = tmp_path / "config.yaml"
        original = "version: [1\n"
        config_path.write_text(original, encoding="utf-8")

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            pytest.raises(ConfigResetRequiredError, match="invalid YAML"),
        ):
            Configuration()

        assert config_path.read_text(encoding="utf-8") == original
        assert "Migrating" not in capsys.readouterr().err
