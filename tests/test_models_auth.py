"""Comprehensive tests for the authentication configuration module."""

import math
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

from pydantic import AnyHttpUrl, AnyUrl

from canfar.models.auth import (
    OIDC,
    X509,
    Client,
    Endpoint,
    Expiry,
    Token,
)
from canfar.models.http import Server


class TestOIDCURLConfig:
    """Test OIDC URL configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC URL configuration."""
        config = Endpoint()
        assert config.discovery is None
        assert config.device is None
        assert config.registration is None
        assert config.token is None

    def test_with_values(self) -> None:
        """Test OIDC URL configuration with values."""
        config = Endpoint(
            discovery="https://example.com/.well-known/openid-configuration",
            device="https://example.com/device",
            registration="https://example.com/register",
            token="https://example.com/token",  # nosec B106
        )
        assert (
            config.discovery == "https://example.com/.well-known/openid-configuration"
        )
        assert config.device == "https://example.com/device"
        assert config.registration == "https://example.com/register"
        assert config.token == "https://example.com/token"  # nosec B105


class TestOIDCClientConfig:
    """Test OIDC client configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC client configuration."""
        config = Client()
        assert config.identity is None
        assert config.secret is None

    def test_with_values(self) -> None:
        """Test OIDC client configuration with values."""
        config = Client(
            identity="test_client_id",
            secret="test_client_secret",  # nosec B106
        )
        assert config.identity == "test_client_id"
        assert config.secret == "test_client_secret"  # nosec B105


class TestOIDCTokenConfig:
    """Test OIDC token configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC token configuration."""
        config = Token()
        assert config.access is None
        assert config.refresh is None

    def test_with_values(self) -> None:
        """Test OIDC token configuration with values."""
        config = Token(
            access="test_access_token",
            refresh="test_refresh_token",
        )
        assert config.access == "test_access_token"
        assert config.refresh == "test_refresh_token"


class TestOIDCExpiryConfig:
    """Test OIDC expiry configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC expiry configuration."""
        config = Expiry()
        assert config.access is None
        assert config.refresh is None

    def test_with_values(self) -> None:
        """Test OIDC expiry configuration with values."""
        future_time = time.time() + 3600
        config = Expiry(
            access=future_time,
            refresh=future_time + 3600,
        )
        assert config.access == future_time
        assert config.refresh == future_time + 3600


class TestOIDC:
    """Test complete OIDC configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC configuration."""
        config = OIDC()
        assert isinstance(config.endpoints, Endpoint)
        assert isinstance(config.client, Client)
        assert isinstance(config.token, Token)
        assert isinstance(config.server, Server)
        assert isinstance(config.expiry, Expiry)

    def test_valid_with_missing_fields(self) -> None:
        """Test valid method with missing required fields."""
        config = OIDC()
        assert not config.valid

    def test_valid_with_partial_fields(self) -> None:
        """Test valid method with some required fields missing."""
        config = OIDC()
        config.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.endpoints.token = "https://example.com/token"  # nosec B105
        config.client.identity = "test_client_id"
        # Missing client.secret, token.refresh, token.expiry
        assert not config.valid

    def test_valid_with_all_required_fields(self) -> None:
        """Test valid method with all required fields present."""
        config = OIDC()
        config.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.endpoints.token = "https://example.com/token"  # nosec B105
        config.client.identity = "test_client_id"
        config.client.secret = "test_client_secret"  # nosec B105
        config.token.refresh = "test_refresh_token"
        assert config.valid

    def test_expired_no_access_token(self) -> None:
        """Test expired property when access token is None."""
        config = OIDC()
        assert config.expired is True

    def test_expired_no_expiry(self) -> None:
        """Test expired property when expiry is None."""
        config = OIDC()
        config.token.refresh = "test_refresh_token"
        assert config.expired is True

    def test_expired_token_expired(self) -> None:
        """Test expired property when token is expired."""
        past_time = time.time() - 3600
        config = OIDC()
        config.token.refresh = "test_refresh_token"
        config.expiry.refresh = past_time
        assert config.expired is True

    def test_expired_token_valid(self) -> None:
        """Test expired property when token is still valid."""
        future_time = time.time() + 3600
        config = OIDC()
        config.token.access = "test_refresh_token"
        config.expiry.access = future_time
        assert config.expired is False


class TestX509:
    """Test X.509 certificate configuration."""

    def test_default_values(self) -> None:
        """Test default values for X.509 configuration."""
        config = X509()
        assert config.path is None
        assert math.isclose(config.expiry, 0.0, abs_tol=1e-9)

    def test_with_values(self) -> None:
        """Test X.509 configuration with values."""
        future_time = time.time() + 3600
        config = X509(
            path="/path/to/cert.pem",
            expiry=future_time,
        )
        assert str(config.path) == "/path/to/cert.pem"
        assert config.expiry == future_time

    def test_valid_no_path(self) -> None:
        """Test valid method when path is None."""
        config = X509()
        assert not config.valid

    def test_valid_path_exists_with_expiry(self) -> None:
        """Test valid method when path exists and expiry is set."""
        future_time = time.time() + 3600
        with NamedTemporaryFile() as temp_file:
            config = X509(path=Path(temp_file.name), expiry=future_time)
            assert config.valid

    def test_expired_no_expiry(self) -> None:
        """Test expired property when expiry is None."""
        config = X509()
        assert config.expired is True

    def test_expired_certificate_expired(self) -> None:
        """Test expired property when certificate is expired."""
        past_time = time.time() - 3600
        config = X509(expiry=past_time)
        assert config.expired is True

    def test_expired_certificate_valid(self) -> None:
        """Test expired property when certificate is still valid."""

    future_time = time.time() + 3600
    with NamedTemporaryFile() as temp_file:
        config = X509(path=Path(temp_file.name), expiry=future_time)
        assert config.expired is False


class TestServerInfo:
    """Test server information configuration."""

    def test_default_values(self) -> None:
        """Test default values for ServerInfo."""
        server = Server()
        assert server.name is None
        assert server.uri is None
        assert server.url is None

    def test_with_values(self) -> None:
        """Test ServerInfo with custom values."""
        server = Server(
            name="Test Server",
            uri=AnyUrl("ivo://test.example.com/skaha"),
            url=AnyHttpUrl("https://test.example.com/skaha"),
        )
        assert server.name == "Test Server"
        assert str(server.uri) == "ivo://test.example.com/skaha"
        assert str(server.url) == "https://test.example.com/skaha"

    def test_partial_values(self) -> None:
        """Test ServerInfo with partial values."""
        server = Server(name="Test Server")
        assert server.name == "Test Server"
        assert server.uri is None
        assert server.url is None


class TestOIDCWithServer:
    """Test OIDC configuration with server information."""

    def test_default_server_field(self) -> None:
        """Test that OIDC has a default server field."""
        oidc = OIDC()
        assert isinstance(oidc.server, Server)
        assert oidc.server.name is None
        assert oidc.server.uri is None
        assert oidc.server.url is None

    def test_with_server_info(self) -> None:
        """Test OIDC with server information."""
        server_info = Server(
            name="Canada",
            uri=AnyUrl("ivo://canfar.net/src/skaha"),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        )
        oidc = OIDC(server=server_info)
        assert oidc.server.name == "Canada"
        assert str(oidc.server.uri) == "ivo://canfar.net/src/skaha"
        assert str(oidc.server.url) == "https://ws-uv.canfar.net/skaha"

    def test_server_field_serialization(self) -> None:
        """Test that OIDC server field is properly serialized."""
        server_info = Server(
            name="Test Server",
            uri=AnyUrl("ivo://test.example.com/skaha"),
            url=AnyHttpUrl("https://test.example.com/skaha"),
        )
        oidc = OIDC(server=server_info)

        # Test model dump includes server field
        data = oidc.model_dump()
        assert "server" in data
        assert data["server"]["name"] == "Test Server"
        assert str(data["server"]["uri"]) == "ivo://test.example.com/skaha"
        assert str(data["server"]["url"]) == "https://test.example.com/skaha"


class TestX509WithServer:
    """Test X509 configuration with server information."""

    def test_default_server_field(self) -> None:
        """Test that X509 has a default server field."""
        x509 = X509()
        assert x509.server is None

    def test_with_server_info(self) -> None:
        """Test X509 with server information."""
        server_info = Server(
            name="CANFAR",
            uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        )
        x509 = X509(server=server_info)
        assert x509.server.name == "CANFAR"
        assert str(x509.server.uri) == "ivo://cadc.nrc.ca/skaha"
        assert str(x509.server.url) == "https://ws-uv.canfar.net/skaha"

    def test_server_field_serialization(self) -> None:
        """Test that X509 server field is properly serialized."""
        server_info = Server(
            name="Test Server",
            uri=AnyUrl("ivo://test.example.com/skaha"),
            url=AnyHttpUrl("https://test.example.com/skaha"),
        )
        x509 = X509(server=server_info)

        # Test model dump includes server field
        data = x509.model_dump()
        assert "server" in data
        assert data["server"]["name"] == "Test Server"
        assert str(data["server"]["uri"]) == "ivo://test.example.com/skaha"
        assert str(data["server"]["url"]) == "https://test.example.com/skaha"
