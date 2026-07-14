"""Comprehensive tests for the authentication configuration module."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import AnyHttpUrl, AnyUrl

from canfar.models.auth import (
    Authentication,
    Client,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
    X509Credential,
)
from canfar.models.http import Server


class TestAuthenticationModel:
    """Test Authentication domain record."""

    def test_model_dump_includes_null_fields(self) -> None:
        """Serialization keeps declared null fields for stable machine keys."""
        record = Authentication(
            idp="cadc",
            name="CADC",
            mode="x509",
            expiry=None,
            active=True,
            server=None,
        )
        payload = record.model_dump(mode="json", exclude_none=False)
        assert set(payload) == {"idp", "name", "mode", "expiry", "active", "server"}
        assert payload["server"] is None


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
        assert config.secret is not None
        assert config.secret.get_secret_value() == "test_client_secret"  # nosec B105


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
        assert config.access is not None
        assert config.access.get_secret_value() == "test_access_token"
        assert config.refresh is not None
        assert config.refresh.get_secret_value() == "test_refresh_token"


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


class TestCanonicalCredentialEligibility:
    """Boundary contracts for canonical Authentication Record eligibility."""

    @staticmethod
    def oidc(refresh_expiry: float | None = None) -> OIDCCredential:
        """Build a complete canonical OIDC Authentication Record."""
        return OIDCCredential(
            idp="test",
            endpoints=Endpoint(
                discovery="https://identity.example/.well-known/openid-configuration",
                token="https://identity.example/token",
            ),
            client=Client(identity="client", secret="secret"),
            token=Token(access="access", refresh="refresh"),
            expiry=Expiry(access=2_000.0, refresh=refresh_expiry),
        )

    @pytest.mark.parametrize(
        ("expiry", "expired"),
        [(None, True), (0.0, True), (1_000.0, True), (1_001.0, False)],
    )
    def test_oidc_access_expiry_boundaries(
        self,
        expiry: float | None,
        expired: bool,
    ) -> None:
        """Missing, zero, and exact access expiry are expired."""
        credential = self.oidc()
        credential.expiry.access = expiry

        with patch("canfar.models.auth.time.time", return_value=1_000.0):
            assert credential.expired is expired

    @pytest.mark.parametrize(
        ("expiry", "refreshable"),
        [(None, True), (0.0, False), (1_000.0, False), (1_001.0, True)],
    )
    def test_oidc_refresh_expiry_boundaries(
        self,
        expiry: float | None,
        refreshable: bool,
    ) -> None:
        """Only missing or future refresh expiry remains eligible."""
        credential = self.oidc(expiry)

        with patch("canfar.models.auth.time.time", return_value=1_000.0):
            assert credential.refreshable is refreshable

    @pytest.mark.parametrize(
        ("expiry", "expired"),
        [(1_000.0, True), (1_001.0, False)],
    )
    def test_x509_expiry_boundaries(self, expiry: float, expired: bool) -> None:
        """An X.509 Authentication Record expires exactly at its boundary."""
        credential = X509Credential(
            idp="test",
            path=Path("/unused/cert.pem"),
            expiry=expiry,
        )

        with patch("canfar.models.auth.time.time", return_value=1_000.0):
            assert credential.expired is expired


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
