"""Comprehensive tests for the Configuration model (V2)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl, ValidationError

from canfar.models.auth import OIDC, X509, Client, Endpoint, Expiry, Token
from canfar.models.config import Configuration
from canfar.models.http import Server
from canfar.models.registry import ContainerRegistry


class TestConfigurationDefaults:
    """Test default state and initialization."""

    def test_default_initialization(self) -> None:
        """Test Configuration with correct defaults when no arguments provided."""
        config = Configuration()

        # Test default active context
        assert config.active == "default"

        # Test default contexts structure
        assert isinstance(config.contexts, dict)
        assert "default" in config.contexts
        assert len(config.contexts) == 1

        # Test default context is X509
        default_context = config.contexts["default"]
        assert isinstance(default_context, X509)
        assert default_context.mode == "x509"

        # Test default X509 configuration
        assert default_context.path == Path.home() / ".ssl" / "cadcproxy.pem"
        # Note: expiry may be computed from actual cert file if it exists
        assert isinstance(default_context.expiry, float)

        # Test default server configuration
        assert isinstance(default_context.server, Server)
        assert default_context.server.name == "CADC-CANFAR"
        assert str(default_context.server.uri) == "ivo://cadc.nrc.ca/skaha"
        assert str(default_context.server.url) == "https://ws-uv.canfar.net/skaha"
        assert default_context.server.version == "v1"

        # Test default registry
        assert isinstance(config.registry, ContainerRegistry)
        assert config.registry.url is None
        assert config.registry.username is None
        assert config.registry.secret is None

    def test_model_config_settings(self) -> None:
        """Test model configuration settings are properly applied."""
        # Test extra fields are forbidden
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            Configuration(invalid_field="value")  # type: ignore[call-arg]

        # Test case insensitive environment variable handling
        with patch.dict(os.environ, {"CANFAR_ACTIVE": "test"}):
            # This should work even though we use lowercase in the model
            config = Configuration(contexts={"test": X509(expiry=1234567890.0)})
            assert config.active == "test"


class TestConfigurationValidation:
    """Test data integrity and validation."""

    def test_valid_active_context(self) -> None:
        """Test validation passes when active context exists in contexts."""
        contexts = {
            "test": X509(path=Path("/test/cert.pem"), expiry=1234567890.0),
            "prod": OIDC(
                endpoints=Endpoint(),
                client=Client(),
                token=Token(),
                server=Server(),
                expiry=Expiry(),
            ),
        }

        # Should work with existing context
        config = Configuration(active="test", contexts=contexts)
        assert config.active == "test"

        # Should work with different existing context
        config = Configuration(active="prod", contexts=contexts)
        assert config.active == "prod"

    def test_invalid_active_context(self) -> None:
        """Test validation fails when active context doesn't exist in contexts."""
        contexts = {
            "test": X509(path=Path("/test/cert.pem"), expiry=1234567890.0),
            "prod": OIDC(
                endpoints=Endpoint(),
                client=Client(),
                token=Token(),
                server=Server(),
                expiry=Expiry(),
            ),
        }

        with pytest.raises(
            ValidationError, match="Active context 'nonexistent' not found"
        ):
            Configuration(active="nonexistent", contexts=contexts)

    def test_custom_active_with_matching_context(self) -> None:
        """Test validation succeeds with custom active and matching context."""
        custom_context = X509(
            path=Path("/custom/cert.pem"),
            expiry=1234567890.0,
            server=Server(
                name="Custom Server",
                uri=AnyUrl("ivo://custom.org/skaha"),
                url=AnyHttpUrl("https://custom.org/skaha"),
                version="v1",
            ),
        )

        config = Configuration(
            active="custom",
            contexts={"custom": custom_context},
        )

        assert config.active == "custom"
        assert config.contexts["custom"] == custom_context


class TestConfigurationSerialization:
    """Test save/load functionality and round-trip serialization."""

    def test_complex_round_trip_serialization(self, tmp_path: Path) -> None:
        """Test complex configuration can be saved and perfectly loaded back."""
        # Create complex configuration with multiple contexts
        oidc_context = OIDC(
            endpoints=Endpoint(
                discovery="https://oidc.example.com/.well-known/openid_configuration",
                token="https://oidc.example.com/token",
                device="https://oidc.example.com/device",
                registration="https://oidc.example.com/register",
            ),
            client=Client(
                identity="test-client-id",
                secret="test-client-secret",
            ),
            token=Token(
                access="test-access-token",
                refresh="test-refresh-token",
            ),
            server=Server(
                name="OIDC-Server",
                uri=AnyUrl("ivo://oidc.example.com/skaha"),
                url=AnyHttpUrl("https://oidc.example.com/skaha"),
                version="v2",
            ),
            expiry=Expiry(
                access=1234567890.0,
                refresh=1234567890.0,
            ),
        )

        x509_context = X509(
            path=Path("/custom/path/cert.pem"),
            expiry=9876543210.0,
            server=Server(
                name="X509-Server",
                uri=AnyUrl("ivo://x509.example.com/skaha"),
                url=AnyHttpUrl("https://x509.example.com/skaha"),
                version="v3",
            ),
        )

        registry = ContainerRegistry(
            url=AnyHttpUrl("https://registry.example.com"),
            username="test-user",
            secret="test-secret",
        )

        # Create configuration with non-default active context
        original_config = Configuration(
            active="OIDC-Server",
            contexts={
                "OIDC-Server": oidc_context,
                "X509-Server": x509_context,
            },
            registry=registry,
        )

        # Save to temporary file
        temp_config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            original_config.save()

            # Load from temporary file
            loaded_config = Configuration()

        # Assert perfect equivalence
        assert loaded_config.active == original_config.active
        assert loaded_config.active == "OIDC-Server"

        # Assert contexts match
        assert set(loaded_config.contexts.keys()) == set(
            original_config.contexts.keys()
        )
        assert "OIDC-Server" in loaded_config.contexts
        assert "X509-Server" in loaded_config.contexts

        # Assert OIDC context details
        loaded_oidc = loaded_config.contexts["OIDC-Server"]
        assert isinstance(loaded_oidc, OIDC)
        assert loaded_oidc.endpoints.discovery == oidc_context.endpoints.discovery
        assert loaded_oidc.client.identity == oidc_context.client.identity
        assert loaded_oidc.token.access == oidc_context.token.access
        assert loaded_oidc.server.name == oidc_context.server.name

        # Assert X509 context details
        loaded_x509 = loaded_config.contexts["X509-Server"]
        assert isinstance(loaded_x509, X509)
        assert loaded_x509.path == x509_context.path
        assert loaded_x509.expiry == x509_context.expiry
        if loaded_x509.server is not None and x509_context.server is not None:
            assert loaded_x509.server.name == x509_context.server.name

        # Assert registry details
        assert loaded_config.registry.url == registry.url
        assert loaded_config.registry.username == registry.username
        assert loaded_config.registry.secret == registry.secret

    def test_save_creates_directory(self, tmp_path: Path) -> None:
        """Test save method creates parent directories if they don't exist."""
        config = Configuration()
        nested_path = tmp_path / "nested" / "config.yaml"

        with patch("canfar.models.config.CONFIG_PATH", nested_path):
            config.save()

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_yaml_file_content_structure(self, tmp_path: Path) -> None:
        """Test saved YAML file has correct structure and content."""
        config = Configuration(
            active="test",
            contexts={"test": X509(path=Path("/test.pem"), expiry=1234567890.0)},
        )

        temp_config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config.save()

        # Read and verify YAML content
        with temp_config_path.open(encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        assert yaml_data["active"] == "test"
        assert "contexts" in yaml_data
        assert "test" in yaml_data["contexts"]
        assert yaml_data["contexts"]["test"]["mode"] == "x509"
        assert "registry" in yaml_data


class TestConfigurationContext:
    """Test context property functionality."""

    def test_context_property_returns_active_context(self) -> None:
        """Test context property returns the currently active AuthContext object."""
        x509_context = X509(path=Path("/test.pem"), expiry=1234567890.0)
        oidc_context = OIDC(
            endpoints=Endpoint(),
            client=Client(),
            token=Token(),
            server=Server(),
            expiry=Expiry(),
        )

        config = Configuration(
            active="x509",
            contexts={
                "x509": x509_context,
                "oidc": oidc_context,
            },
        )

        # Should return X509 context when active is "x509"
        assert config.context is x509_context
        assert isinstance(config.context, X509)

        # Change active context
        config.active = "oidc"

        # Should now return OIDC context
        assert config.context is oidc_context
        assert isinstance(config.context, OIDC)

    def test_context_property_with_default(self) -> None:
        """Test context property works with default configuration."""
        config = Configuration()

        context = config.context
        assert isinstance(context, X509)
        assert context.mode == "x509"
        assert context is config.contexts["default"]


class TestConfigurationSettingsPrecedence:
    """Test layered settings precedence."""

    def test_environment_overrides_yaml_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test environment variables take precedence over YAML file settings."""
        # Create temporary config file with one active value
        config_data: dict[str, Any] = {
            "active": "yaml_default",
            "contexts": {
                "yaml_default": {
                    "mode": "x509",
                    "path": "/yaml/cert.pem",
                    "expiry": 1234567890.0,
                },
                "env_override": {
                    "mode": "x509",
                    "path": "/env/cert.pem",
                    "expiry": 9876543210.0,
                },
            },
        }

        temp_config_path = tmp_path / "config.yaml"
        with temp_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # Set environment variable to override
        monkeypatch.setenv("CANFAR_ACTIVE", "env_override")

        # Load configuration
        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config = Configuration()

        # Environment variable should take precedence
        assert config.active == "env_override"

        # Verify the context exists and is correct
        assert "env_override" in config.contexts
        assert isinstance(config.contexts["env_override"], X509)

    def test_init_args_override_all_sources(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test init arguments override both environment and file settings."""
        # Create temporary config file
        config_data: dict[str, Any] = {
            "active": "yaml_default",
            "contexts": {
                "yaml_default": {
                    "mode": "x509",
                    "path": "/yaml/cert.pem",
                    "expiry": 1234567890.0,
                },
                "env_override": {
                    "mode": "x509",
                    "path": "/env/cert.pem",
                    "expiry": 9876543210.0,
                },
                "init_override": {
                    "mode": "x509",
                    "path": "/init/cert.pem",
                    "expiry": 5555555555.0,
                },
            },
        }

        temp_config_path = tmp_path / "config.yaml"
        with temp_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # Set environment variable
        monkeypatch.setenv("CANFAR_ACTIVE", "env_override")

        # Load configuration with init args
        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config = Configuration(active="init_override")

        # Init args should take highest precedence
        assert config.active == "init_override"

    def test_yaml_loads_when_no_env_or_init(self, tmp_path: Path) -> None:
        """Test YAML file settings are used when no environment or init overrides."""
        config_data: dict[str, Any] = {
            "active": "yaml_context",
            "contexts": {
                "yaml_context": {
                    "mode": "x509",
                    "path": "/yaml/cert.pem",
                    "expiry": 1234567890.0,
                },
            },
            "registry": {
                "url": "https://yaml.registry.com",
                "username": "yaml_user",
                "secret": "yaml_secret",
            },
        }

        temp_config_path = tmp_path / "config.yaml"
        with temp_config_path.open("w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        with patch("canfar.models.config.CONFIG_PATH", temp_config_path):
            config = Configuration()

        assert config.active == "yaml_context"
        assert config.registry.username == "yaml_user"
        # URL may have trailing slash added by pydantic
        assert str(config.registry.url).rstrip("/") == "https://yaml.registry.com"


class TestConfigurationErrorHandling:
    """Test error handling scenarios."""

    def test_save_handles_directory_creation_error(self, tmp_path: Path) -> None:
        """Test save method handles directory creation errors gracefully."""
        config = Configuration()

        # Mock pathlib.Path.mkdir to raise an OSError
        config_path = tmp_path / "blocked" / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")),
            pytest.raises(OSError, match="Permission denied"),
        ):
            config.save()

    def test_save_handles_file_write_error(self, tmp_path: Path) -> None:
        """Test save method handles file write errors gracefully."""
        config = Configuration()

        # Create a directory where we want to write a file (will cause OSError)
        config_path = tmp_path / "config.yaml"
        config_path.mkdir()  # Make it a directory instead of a file

        error_msg = f"Failed to save configuration to {config_path}"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            pytest.raises(OSError, match=error_msg),
        ):
            config.save()

    def test_save_handles_yaml_serialization_error(self, tmp_path: Path) -> None:
        """Test save method handles YAML serialization errors."""
        config = Configuration()
        config_path = tmp_path / "config.yaml"

        # Mock yaml.dump to raise an error
        error_msg = f"Failed to save configuration to {config_path}"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("yaml.dump", side_effect=TypeError("Mock YAML error")),
            pytest.raises(OSError, match=error_msg),
        ):
            config.save()

    def test_settings_customise_sources_order(self) -> None:
        """Test settings sources are ordered correctly for precedence."""
        sources = Configuration.settings_customise_sources(
            Configuration,
            init_settings=None,  # type: ignore[arg-type]
            env_settings=None,  # type: ignore[arg-type]
            dotenv_settings=None,  # type: ignore[arg-type]
            file_secret_settings=None,  # type: ignore[arg-type]
        )

        # Should return 4 sources in correct precedence order
        assert len(sources) == 4

        # First should be init_settings (highest precedence)
        # Second should be env_settings
        # Third should be YamlConfigSettingsSource
        # Fourth should be file_secret_settings (lowest precedence)
        assert sources[0] is None  # init_settings (mocked as None)
        assert sources[1] is None  # env_settings (mocked as None)
        # sources[2] should be YamlConfigSettingsSource instance
        assert sources[3] is None  # file_secret_settings (mocked as None)
