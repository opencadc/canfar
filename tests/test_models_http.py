"""Comprehensive tests for the HTTP models module."""

import pytest
from pydantic import ValidationError

from canfar.models.http import Server


class TestServer:
    """Test Server class."""

    def test_model_ignores_environment_and_has_no_network_methods(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Persisted Server data comes only from validated input."""
        monkeypatch.setenv("CANFAR_SERVER_NAME", "Environment Server")
        monkeypatch.setenv("CANFAR_SERVER_CORES", "64")

        server = Server()

        assert server.name is None
        assert server.cores == 2
        assert not hasattr(server, "capabilities")
        assert not hasattr(server, "fetch")
        assert not hasattr(server, "afetch")

    def test_default_values(self) -> None:
        """Test default values for Server."""
        server = Server()
        assert server.name is None
        assert server.uri is None
        assert server.url is None
        assert server.version is None
        assert server.status is None

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

        server = Server(version="v2.1")
        assert server.version == "v2.1"

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
