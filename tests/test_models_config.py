"""Comprehensive tests for the Configuration model."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl, ValidationError

from canfar.models.active import ActiveConfig
from canfar.models.auth import (
    Client,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
    X509Credential,
)
from canfar.models.config import Configuration, _CanfarEnvSettingsSource
from canfar.models.http import Server, VOSpaceService
from canfar.models.registry import ContainerRegistry


def _sample_config(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "version": 1,
        "active": {
            "authentication": "cadc",
            "server": "canfar",
        },
        "authentication": {
            "cadc": {
                "mode": "x509",
                "path": "/test/cert.pem",
                "expiry": 1234567890.0,
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
    payload.update(overrides)
    return payload


class TestConfigurationDefaults:
    """Test default state and initialization."""

    def test_default_servers_dict_keyed_by_server_name(self, tmp_path: Path) -> None:
        """Default Science Platform Servers are keyed by Server Name."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert set(config.servers) == {"canfar"}
        assert config.servers["canfar"].name == "canfar"
        dumped = config.model_dump(mode="json", exclude_none=True)
        assert dumped["servers"]["canfar"]["name"] == "canfar"

    def test_default_authentication_dict_keyed_by_idp(self, tmp_path: Path) -> None:
        """Default Authentication Records are keyed by IDP."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert set(config.authentication) == {"cadc"}
        assert isinstance(config.authentication["cadc"], X509Credential)
        assert config.authentication["cadc"].idp == "cadc"
        dumped = config.model_dump(mode="json", exclude_none=True)
        assert dumped["authentication"]["cadc"]["idp"] == "cadc"

    def test_default_initialization(self, tmp_path: Path) -> None:
        """Configuration defaults to the CADC placeholder when no file exists."""
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 1
        assert config.active.authentication == "cadc"
        assert config.active.server == "canfar"
        assert set(config.authentication) == {"cadc"}
        assert isinstance(config.authentication["cadc"], X509Credential)
        assert set(config.servers) == {"canfar"}
        assert config.servers["canfar"].name == "canfar"
        assert isinstance(config.registry, ContainerRegistry)

    def test_model_config_settings(self) -> None:
        """Extra fields are forbidden on the configuration model."""
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            Configuration(invalid_field="value")  # type: ignore[call-arg]


class TestConfigurationValidation:
    """Test data integrity and validation."""

    @pytest.mark.parametrize(
        "server_name",
        ["1bad", "bad.name", ""],
    )
    def test_invalid_server_name_key_rejected(self, server_name: str) -> None:
        """Invalid Server Name keys fail validation with a clear message."""
        with pytest.raises(ValidationError, match="Invalid server name"):
            Configuration(
                servers={
                    server_name: Server(
                        idp="cadc",
                        uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
                        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
                        version="v1",
                    ),
                },
            )

    @pytest.mark.parametrize(
        "idp_key",
        ["1bad", "bad.key", ""],
    )
    def test_invalid_idp_key_rejected(self, idp_key: str) -> None:
        """Invalid IDP keys fail validation with a clear message."""
        with pytest.raises(ValidationError, match="Invalid IDP key"):
            Configuration(
                authentication={
                    idp_key: X509Credential(
                        idp=idp_key or "cadc",
                        path=Path("/test/cert.pem"),
                        expiry=1.0,
                    ),
                },
            )

    @pytest.mark.parametrize(
        "storage_name",
        [
            "",
            "local",
            " local ",
            "archive:old",
            "archive\x00old",
            "archive\nold",
            "archive\n",
            "archive\r",
            "archive\r\n",
            "-archive",
        ],
    )
    def test_invalid_storage_name_rejected(
        self, storage_name: str, tmp_path: Path
    ) -> None:
        """Invalid Storage Names fail with the rejected name and constraints."""
        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            pytest.raises(ValidationError, match="Invalid Storage Name") as exc_info,
        ):
            Configuration.model_validate(
                {
                    "servers": {
                        "canfar": {
                            "storage": {
                                storage_name: {
                                    "uri": "ivo://cadc.nrc.ca/arc",
                                    "url": "https://ws-cadc.canfar.net/arc",
                                }
                            }
                        }
                    }
                }
            )

        assert repr(storage_name) in str(exc_info.value)

    def test_long_storage_name_allowed(self) -> None:
        """Storage Names do not inherit Server field length limits."""
        storage_name = "a" * 257
        service = {
            "uri": "ivo://cadc.nrc.ca/arc",
            "url": "https://ws-cadc.canfar.net/arc",
        }

        server = Server(storage={storage_name: service})

        assert list(server.storage) == [storage_name]

    def test_storage_name_whitespace_is_trimmed(self) -> None:
        """Valid surrounding whitespace remains normalized."""
        service = {
            "uri": "ivo://cadc.nrc.ca/arc",
            "url": "https://ws-cadc.canfar.net/arc",
        }

        assert list(Server(storage={" arc ": service}).storage) == ["arc"]

    def test_duplicate_storage_name_across_servers_rejected(
        self, tmp_path: Path
    ) -> None:
        """A Storage Name identifies one service across Science Platform Servers."""
        service = VOSpaceService(
            uri="ivo://cadc.nrc.ca/arc",
            url="https://ws-cadc.canfar.net/arc",
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            pytest.raises(
                ValidationError,
                match=(
                    "Duplicate Storage Name 'shared' in Science Platform Servers "
                    "'canfar' and 'srcnet'"
                ),
            ),
        ):
            Configuration.model_validate(
                {
                    "servers": {
                        "canfar": Server(storage={"shared": service}),
                        "srcnet": Server(storage={"shared": service}),
                    }
                }
            )

    def test_normalized_storage_name_collision_rejected(self) -> None:
        """Whitespace normalization cannot silently replace a VOSpace Service."""
        service = {
            "uri": "ivo://cadc.nrc.ca/arc",
            "url": "https://ws-cadc.canfar.net/arc",
        }

        with pytest.raises(
            ValidationError,
            match="Storage Names 'arc' and ' arc ' both normalize to 'arc'",
        ):
            Server(storage={"arc": service, " arc ": service})

    def test_valid_active_references(self) -> None:
        """Validation passes when active authentication and server exist."""
        config = Configuration(
            active=ActiveConfig(
                authentication="cadc",
                server="canfar",
            ),
            authentication={
                "cadc": X509Credential(
                    idp="cadc", path=Path("/test/cert.pem"), expiry=1.0
                ),
            },
            servers={
                "canfar": Server(
                    idp="cadc",
                    uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
                    url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
                    version="v1",
                ),
            },
        )
        assert config.active.authentication == "cadc"
        assert config.active.server == "canfar"

    def test_invalid_active_authentication(self) -> None:
        """Validation fails when active authentication is unknown."""
        with pytest.raises(
            ValidationError,
            match="Active authentication 'missing' not found",
        ):
            Configuration(
                active=ActiveConfig(
                    authentication="missing",
                    server="canfar",
                ),
                authentication={
                    "cadc": X509Credential(
                        idp="cadc", path=Path("/test/cert.pem"), expiry=1.0
                    ),
                },
                servers={
                    "canfar": Server(
                        idp="cadc",
                        uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
                        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
                        version="v1",
                    ),
                },
            )

    def test_invalid_active_server(self) -> None:
        """Validation fails when active Server Name is unknown."""
        with pytest.raises(
            ValidationError,
            match=r"Active server 'missing' not found",
        ):
            Configuration(
                active=ActiveConfig(
                    authentication="cadc",
                    server="missing",
                ),
                authentication={
                    "cadc": X509Credential(
                        idp="cadc", path=Path("/test/cert.pem"), expiry=1.0
                    ),
                },
                servers={
                    "canfar": Server(
                        idp="cadc",
                        uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
                        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
                        version="v1",
                    ),
                },
            )

    def test_invalid_remembered_server_name(self) -> None:
        """Validation fails when remembered selection names a missing server."""
        with pytest.raises(
            ValidationError,
            match=r"Remembered server 'missing' not found",
        ):
            Configuration(
                active=ActiveConfig(
                    authentication="cadc",
                    server="canfar",
                    servers={"cadc": "missing"},
                ),
                authentication={
                    "cadc": X509Credential(
                        idp="cadc", path=Path("/test/cert.pem"), expiry=1.0
                    ),
                },
                servers={
                    "canfar": Server(
                        idp="cadc",
                        uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
                        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
                        version="v1",
                    ),
                },
            )


class TestConfigurationSerialization:
    """Test save/load functionality and round-trip serialization."""

    def test_complex_round_trip_serialization(self, tmp_path: Path) -> None:
        """Complex configuration can be saved and loaded back."""
        oidc = OIDCCredential(
            idp="srcnet",
            endpoints=Endpoint(
                discovery="https://example.com/.well-known/openid-configuration",
                token="https://example.com/token",
            ),
            client=Client(identity="client-id", secret="client-secret"),
            token=Token(
                access="access-token",
                refresh="refresh-token",
                token_type="Bearer",
                scope="openid profile email",
            ),
            expiry=Expiry(access=1893456000),
        )
        x509 = X509Credential(
            idp="cadc",
            path=Path("/custom/path/cert.pem"),
            expiry=9876543210.0,
        )
        registry = ContainerRegistry(
            url=AnyHttpUrl("https://registry.example.com"),
            username="test-user",
            secret="test-secret",
        )
        original = Configuration(
            active=ActiveConfig(
                authentication="srcnet",
                server="SRCNet",
            ),
            authentication={"srcnet": oidc, "cadc": x509},
            servers={
                "SRCNet": Server(
                    idp="srcnet",
                    uri=AnyUrl("ivo://srcnet.example/skaha"),
                    url=AnyHttpUrl("https://srcnet.example/skaha"),
                    version="v1",
                    auths=["oidc"],
                ),
                "canfar": Server(
                    idp="cadc",
                    uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
                    url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
                    version="v1",
                    auths=["x509"],
                ),
            },
            registry=registry,
        )

        temp_config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            original.save()
            loaded = Configuration()

        assert loaded.active.authentication == "srcnet"
        assert loaded.registry.username == "test-user"
        loaded_oidc = loaded.authentication["srcnet"]
        assert isinstance(loaded_oidc, OIDCCredential)
        assert loaded_oidc.client.secret is not None
        assert loaded_oidc.client.secret.get_secret_value() == "client-secret"
        assert loaded_oidc.token.access is not None
        assert loaded_oidc.token.access.get_secret_value() == "access-token"
        assert loaded_oidc.token.refresh is not None
        assert loaded_oidc.token.refresh.get_secret_value() == "refresh-token"
        assert loaded_oidc.token.token_type == "Bearer"
        assert loaded_oidc.token.scope == "openid profile email"
        assert loaded_oidc.expiry.access == 1893456000
        assert loaded_oidc.expiry.refresh is None

    def test_v1_storage_json_and_yaml_round_trip(self, tmp_path: Path) -> None:
        """Multiple VOSpace Services retain stable nested Storage Names."""
        config = Configuration.model_validate(
            _sample_config(
                servers={
                    "canfar": {
                        **_sample_config()["servers"]["canfar"],
                        "storage": {
                            "canSRC": {
                                "uri": "ivo://cadc.nrc.ca/arc",
                                "url": "https://ws-cadc.canfar.net/arc",
                            },
                            "canSRCs3": {
                                "uri": "ivo://cadc.nrc.ca/arc-s3",
                                "url": "https://ws-cadc.canfar.net/arc-s3",
                            },
                        },
                    }
                }
            )
        )

        json_data = config.model_dump(mode="json")
        assert list(json_data["servers"]["canfar"]["storage"]) == [
            "canSRC",
            "canSRCs3",
        ]
        assert "name" not in json_data["servers"]["canfar"]["storage"]["canSRC"]
        assert Configuration.model_validate_json(config.model_dump_json()) == config

        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config.save()
            loaded = Configuration()

        assert list(loaded.servers["canfar"].storage) == ["canSRC", "canSRCs3"]
        assert loaded.servers["canfar"].idp == "cadc"
        assert loaded == config

    def test_existing_v1_configuration_without_storage_loads_unchanged(
        self, tmp_path: Path
    ) -> None:
        """The optional storage mapping does not require a schema migration."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.safe_dump(_sample_config()), encoding="utf-8")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()

        assert config.version == 1
        assert config.servers["canfar"].storage == {}

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Save creates parent directories when missing."""
        config = Configuration()
        nested_path = tmp_path / "nested" / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", nested_path):
            config.save()
        assert nested_path.exists()

    def test_failed_serialization_preserves_existing_configuration(
        self, tmp_path: Path
    ) -> None:
        """A failed save cannot truncate the last valid configuration."""
        config = Configuration()
        config_path = tmp_path / "config.yaml"
        original = b"version: 1\nmarker: keep-me\n"
        config_path.write_bytes(original)

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.config.store.yaml.dump",
                side_effect=TypeError("cannot serialize"),
            ),
            pytest.raises(OSError, match="Failed to save configuration"),
        ):
            config.save()

        assert config_path.read_bytes() == original

    def test_invalid_assignment_cannot_replace_last_valid_configuration(
        self,
        tmp_path: Path,
    ) -> None:
        """Saving validates assignment-mutated state before atomic replacement."""
        config_path = tmp_path / "config.yaml"

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.save()
            original = config_path.read_bytes()
            config.active.authentication = "missing"

            with pytest.raises(OSError, match="Failed to save configuration"):
                config.save()

            loaded = Configuration()

        assert config_path.read_bytes() == original
        assert loaded.active.authentication == "cadc"
        assert set(tmp_path.iterdir()) == {config_path}

    def test_failed_replacement_preserves_existing_configuration(
        self, tmp_path: Path
    ) -> None:
        """A failed atomic replacement leaves no partial configuration behind."""
        config = Configuration()
        config_path = tmp_path / "config.yaml"
        original = b"version: 1\nmarker: keep-me\n"
        config_path.write_bytes(original)

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.config.store.Path.replace",
                side_effect=OSError("cannot replace"),
            ),
            pytest.raises(OSError, match="Failed to save configuration"),
        ):
            config.save()

        assert config_path.read_bytes() == original
        assert set(tmp_path.iterdir()) == {config_path}

    def test_failed_first_write_leaves_no_configuration(self, tmp_path: Path) -> None:
        """A failed first save leaves neither a target nor temporary file."""
        config = Configuration()
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.config.store.os.fsync", side_effect=OSError("disk full")),
            pytest.raises(OSError, match="Failed to save configuration"),
        ):
            config.save()

        assert not config_path.exists()
        assert list(tmp_path.iterdir()) == []

    def test_yaml_file_content_structure(self, tmp_path: Path) -> None:
        """Saved YAML uses current top-level keys."""
        temp_config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config = Configuration(
                authentication={
                    "cadc": X509Credential(
                        idp="cadc", path=Path("/test.pem"), expiry=1234567890.0
                    ),
                },
            )
            config.save()

        yaml_data = yaml.safe_load(temp_config_path.read_text(encoding="utf-8"))
        assert yaml_data["version"] == 1
        assert yaml_data["active"]["authentication"] == "cadc"
        assert yaml_data["authentication"]["cadc"]["mode"] == "x509"
        assert yaml_data["authentication"]["cadc"]["idp"] == "cadc"
        assert yaml_data["servers"]["canfar"]["name"] == "canfar"
        assert "registry" in yaml_data


class TestConfigurationSettingsPrecedence:
    """Test layered settings precedence."""

    def test_nested_active_env_overrides_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nested active env vars override YAML active selection."""
        config_data = _sample_config()
        config_data["servers"]["SRCNet"] = {
            "idp": "srcnet",
            "uri": "ivo://srcnet.example/skaha",
            "url": "https://srcnet.example/skaha",
            "version": "v1",
            "auths": ["oidc"],
        }
        config_data["authentication"]["srcnet"] = {
            "mode": "oidc",
            "endpoints": {},
            "client": {},
            "token": {},
            "expiry": {},
        }
        temp_config_path = tmp_path / "config.yaml"
        temp_config_path.write_text(yaml.dump(config_data), encoding="utf-8")

        monkeypatch.setenv("CANFAR_ACTIVE__AUTHENTICATION", "srcnet")
        monkeypatch.setenv("CANFAR_ACTIVE__SERVER", "SRCNet")

        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config = Configuration()

        assert config.active.authentication == "srcnet"
        assert config.active.server == "SRCNet"

    def test_init_args_override_all_sources(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Init arguments take precedence over env and YAML."""
        temp_config_path = tmp_path / "config.yaml"
        temp_config_path.write_text(yaml.dump(_sample_config()), encoding="utf-8")
        monkeypatch.setenv("CANFAR_ACTIVE__AUTHENTICATION", "srcnet")
        monkeypatch.setenv("CANFAR_ACTIVE__SERVER", "SRCNet")

        override = ActiveConfig(
            authentication="cadc",
            server="canfar",
        )
        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config = Configuration(active=override)

        assert config.active.authentication == "cadc"

    def test_yaml_loads_when_no_env_or_init(self, tmp_path: Path) -> None:
        """YAML settings apply when no env or init overrides exist."""
        config_data = _sample_config(
            registry={
                "url": "https://yaml.registry.com",
                "username": "yaml_user",
                "secret": "yaml_secret",
            },
        )
        temp_config_path = tmp_path / "config.yaml"
        temp_config_path.write_text(yaml.dump(config_data), encoding="utf-8")

        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config = Configuration()

        assert config.registry.username == "yaml_user"
        assert str(config.registry.url).rstrip("/") == "https://yaml.registry.com"


class TestConfigurationErrorHandling:
    """Test error handling scenarios."""

    def test_save_handles_directory_creation_error(self, tmp_path: Path) -> None:
        """Save surfaces directory creation errors."""
        config = Configuration()
        config_path = tmp_path / "blocked" / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")),
            pytest.raises(OSError, match="Permission denied"),
        ):
            config.save()

    def test_save_handles_file_write_error(self, tmp_path: Path) -> None:
        """Save surfaces file write errors."""
        config = Configuration()
        config_path = tmp_path / "config.yaml"
        config_path.mkdir()
        error_msg = f"Failed to save configuration to {config_path}"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            pytest.raises(OSError, match=error_msg),
        ):
            config.save()

    def test_save_handles_yaml_serialization_error(self, tmp_path: Path) -> None:
        """Save surfaces YAML serialization errors."""
        config = Configuration()
        config_path = tmp_path / "config.yaml"
        error_msg = f"Failed to save configuration to {config_path}"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("yaml.dump", side_effect=TypeError("Mock YAML error")),
            pytest.raises(OSError, match=error_msg),
        ):
            config.save()

    def test_settings_customise_sources_order(self) -> None:
        """Settings sources preserve expected precedence ordering."""
        sources = Configuration.settings_customise_sources(
            Configuration,
            init_settings=None,  # type: ignore[arg-type]
            env_settings=None,  # type: ignore[arg-type]
            dotenv_settings=None,  # type: ignore[arg-type]
            file_secret_settings=None,  # type: ignore[arg-type]
        )
        assert len(sources) == 4
        assert sources[0] is None
        assert isinstance(sources[1], _CanfarEnvSettingsSource)
        assert sources[3] is None
