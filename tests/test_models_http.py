"""Comprehensive tests for the HTTP models module."""

import pytest
from pydantic import ValidationError

from canfar.models.http import Connection, Server


class TestServer:
    """Test Server class."""

    def test_default_values(self) -> None:
        """Test default values for Server."""
        server = Server()
        assert server.name is None
        assert server.uri is None
        assert server.url is None
        assert server.version is None

    def test_with_all_values(self) -> None:
        """Test Server with all custom values."""
        server = Server(
            name="Test Server",
            uri="ivo://test.example.com/skaha",
            url="https://test.example.com/skaha",
            version="v1",
        )

        assert server.name == "Test Server"
        assert str(server.uri) == "ivo://test.example.com/skaha"
        assert str(server.url) == "https://test.example.com/skaha"
        assert server.version == "v1"

    def test_with_partial_values(self) -> None:
        """Test Server with partial values."""
        server = Server(name="Partial Server", url="https://example.com")

        assert server.name == "Partial Server"
        assert server.uri is None
        assert str(server.url) == "https://example.com/"  # pydantic adds trailing slash
        assert server.version is None

    def test_name_validation(self) -> None:
        """Test name field validation."""
        # Valid names
        server = Server(name="Valid Name")
        assert server.name == "Valid Name"

        server = Server(name="A" * 256)  # Max length
        assert len(server.name) == 256

        # Invalid names
        with pytest.raises(ValidationError):
            Server(name="")  # Empty string

        with pytest.raises(ValidationError):
            Server(name="A" * 257)  # Too long

    def test_uri_validation(self) -> None:
        """Test URI field validation."""
        # Valid URIs
        server = Server(uri="ivo://example.com/service")
        assert str(server.uri) == "ivo://example.com/service"

        server = Server(uri="https://example.com/path")
        assert str(server.uri) == "https://example.com/path"

        # Invalid URIs
        with pytest.raises(ValidationError):
            Server(uri="not-a-valid-uri")

        with pytest.raises(ValidationError):
            Server(uri="")

    def test_url_validation(self) -> None:
        """Test URL field validation."""
        # Valid URLs
        server = Server(url="https://example.com")
        assert str(server.url) == "https://example.com/"  # pydantic adds trailing slash

        server = Server(url="http://localhost:8080/path")
        assert str(server.url) == "http://localhost:8080/path"

        # Invalid URLs
        with pytest.raises(ValidationError):
            Server(url="not-a-valid-url")

        with pytest.raises(ValidationError):
            Server(url="sftp://example.com")  # Not HTTP/HTTPS

    def test_version_validation(self) -> None:
        """Test version field validation."""
        # Valid versions
        server = Server(version="v0")
        assert server.version == "v0"

        server = Server(version="v123")
        assert server.version == "v123"

        server = Server(version="v9999999")  # Max length test
        assert server.version == "v9999999"

        # Invalid versions
        with pytest.raises(ValidationError):
            Server(version="1")  # Missing 'v' prefix

        with pytest.raises(ValidationError):
            Server(version="version1")  # Wrong format

        with pytest.raises(ValidationError):
            Server(version="v")  # Too short

        with pytest.raises(ValidationError):
            Server(version="v" + "1" * 8)  # Too long

    def test_model_config_settings(self) -> None:
        """Test model configuration settings."""
        # Test that extra fields are forbidden
        with pytest.raises(ValidationError):
            Server(invalid_field="value")

        # Test string stripping
        server = Server(name="  Trimmed Name  ")
        assert server.name == "Trimmed Name"

    def test_examples_from_field_definitions(self) -> None:
        """Test that examples from field definitions work."""
        # Test examples from name field
        server = Server(name="SRCnet-Sweden")
        assert server.name == "SRCnet-Sweden"

        server = Server(name="SRCnet-UK-CAM")
        assert server.name == "SRCnet-UK-CAM"

        # Test examples from URI field
        server = Server(uri="ivo://swesrc.chalmers.se/skaha")
        assert str(server.uri) == "ivo://swesrc.chalmers.se/skaha"

        # Test examples from URL field
        server = Server(url="https://services.swesrc.chalmers.se/skaha")
        assert str(server.url) == "https://services.swesrc.chalmers.se/skaha"


class TestConnection:
    """Test Connection class."""

    def test_default_values(self) -> None:
        """Test default values for Connection."""
        connection = Connection()
        assert connection.concurrency == 32
        assert connection.timeout == 30

    def test_with_custom_values(self) -> None:
        """Test Connection with custom values."""
        connection = Connection(concurrency=64, timeout=60)
        assert connection.concurrency == 64
        assert connection.timeout == 60

    def test_concurrency_validation(self) -> None:
        """Test concurrency field validation."""
        # Valid values
        connection = Connection(concurrency=1)  # Minimum
        assert connection.concurrency == 1

        connection = Connection(concurrency=256)  # Maximum
        assert connection.concurrency == 256

        connection = Connection(concurrency=128)  # Middle value
        assert connection.concurrency == 128

        # Invalid values
        with pytest.raises(ValidationError):
            Connection(concurrency=0)  # Too low

        with pytest.raises(ValidationError):
            Connection(concurrency=257)  # Too high

    def test_timeout_validation(self) -> None:
        """Test timeout field validation."""
        # Valid values
        connection = Connection(timeout=1)  # Minimum (greater than 0)
        assert connection.timeout == 1

        connection = Connection(timeout=300)  # Maximum
        assert connection.timeout == 300

        connection = Connection(timeout=150)  # Middle value
        assert connection.timeout == 150

        # Invalid values
        with pytest.raises(ValidationError):
            Connection(timeout=0)  # Not greater than 0

        with pytest.raises(ValidationError):
            Connection(timeout=-1)  # Negative

        with pytest.raises(ValidationError):
            Connection(timeout=301)  # Too high

    def test_model_config_settings(self) -> None:
        """Test model configuration settings."""
        # Test that extra fields are forbidden
        with pytest.raises(ValidationError):
            Connection(invalid_field="value")

    def test_inheritance_compatibility(self) -> None:
        """Test that Connection can be used as a base class."""
        # This tests that Connection works properly as a base class
        # (as it's used by Configuration)

        class TestConfig(Connection):
            extra_field: str = "test"

        config = TestConfig()
        assert config.concurrency == 32  # Inherited default
        assert config.timeout == 30  # Inherited default
        assert config.extra_field == "test"

        config = TestConfig(concurrency=16, timeout=45)
        assert config.concurrency == 16
        assert config.timeout == 45

    def test_settings_config_dict(self) -> None:
        """Test that settings configuration is properly applied."""
        # Test environment variable prefix and other settings
        connection = Connection()

        # Verify the model config is set correctly
        assert connection.model_config["env_prefix"] == "CANFAR_CONNECTION_"
        assert connection.model_config["case_sensitive"] is False
        assert connection.model_config["extra"] == "forbid"


class TestServerAndConnectionIntegration:
    """Test integration between Server and Connection classes."""

    def test_both_classes_have_compatible_configs(self) -> None:
        """Test that both classes have compatible model configurations."""
        server = Server()
        connection = Connection()

        # Both should forbid extra fields
        assert server.model_config["extra"] == "forbid"
        assert connection.model_config["extra"] == "forbid"

        # Both should be case insensitive
        assert server.model_config["case_sensitive"] is False
        assert connection.model_config["case_sensitive"] is False

        # Both should strip whitespace
        assert server.model_config["str_strip_whitespace"] is True
        assert connection.model_config["str_strip_whitespace"] is True

    def test_realistic_server_configuration(self) -> None:
        """Test a realistic server configuration."""
        server = Server(
            name="CANFAR",
            uri="ivo://cadc.nrc.ca/skaha",
            url="https://ws-uv.canfar.net/skaha",
            version="v0",
        )

        assert server.name == "CANFAR"
        assert str(server.uri) == "ivo://cadc.nrc.ca/skaha"
        assert str(server.url) == "https://ws-uv.canfar.net/skaha"
        assert server.version == "v0"

    def test_realistic_connection_configuration(self) -> None:
        """Test a realistic connection configuration."""
        connection = Connection(concurrency=16, timeout=120)

        assert connection.concurrency == 16
        assert connection.timeout == 120
