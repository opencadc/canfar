"""Tests for the refactored HTTPx authentication hooks."""

import time
from unittest.mock import Mock, patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.client import HTTPClient
from canfar.hooks.httpx.auth import AuthenticationError, arefresh, refresh
from canfar.models.auth import OIDC, X509
from canfar.models.http import Server
from tests.helpers.config import configuration_from_legacy_context
from tests.test_auth_x509 import generate_cert


@pytest.fixture
def oidc_client() -> HTTPClient:
    """Returns a HTTPClient configured with an expired OIDC context.

    The OIDC context is set up to be ready for a token refresh:
    - Access token is expired.
    - Refresh token is valid and present.
    """
    oidc_context = OIDC(
        server=Server(name="TestOIDC", url="https://oidc.example.com", version="v1"),
        endpoints={
            "discovery": "https://oidc.example.com/.well-known/openid-configuration",
            "token": "https://oidc.example.com/token",
        },
        client={"identity": "test-client", "secret": "test-secret"},
        token={"access": "expired-token", "refresh": "valid-refresh-token"},
        expiry={
            "access": time.time() - 60,  # Expired
            "refresh": time.time() + 3600,  # Valid
        },
    )
    config = configuration_from_legacy_context("TestOIDC", oidc_context)
    client = HTTPClient(config=config)
    # Mock the internal httpx clients to check header updates
    client._client = Mock(spec=httpx.Client, headers={})  # noqa: SLF001
    client._asynclient = Mock(spec=httpx.AsyncClient, headers={})  # noqa: SLF001
    return client


class TestSyncHook:
    """Tests for the synchronous `hook` function."""

    @patch("canfar.models.config.Configuration.save")
    @patch("canfar.utils.jwt.expiry", return_value=time.time() + 3600)
    @patch("canfar.auth.oidc.sync_refresh", return_value=SecretStr("new-access-token"))
    def test_successful_refresh(
        self,
        mock_refresh,
        mock_expiry,  # noqa: ARG002
        mock_save,
        oidc_client,
    ) -> None:
        """Verify a successful token refresh updates state and headers."""
        hook_func = refresh(oidc_client)
        request = httpx.Request("GET", "https://oidc.example.com")

        hook_func(request)

        mock_refresh.assert_called_once()
        mock_save.assert_called_once()

        # Verify the request header was updated
        assert request.headers["Authorization"] == "Bearer new-access-token"

        # Verify the main client's headers were updated
        assert oidc_client.client.headers["Authorization"] == "Bearer new-access-token"

        # Verify the context in the config was updated
        new_context = oidc_client.config.context
        assert isinstance(new_context, OIDC)
        assert new_context.token.access is not None
        assert new_context.token.access.get_secret_value() == "new-access-token"
        assert new_context.expiry.access > time.time()

    @patch("canfar.auth.oidc.sync_refresh")
    def test_skip_if_not_oidc_context(self, mock_refresh, tmp_path) -> None:
        """Verify the hook does nothing if active Authentication is not OIDC."""
        cert_path = tmp_path / "cert.pem"
        generate_cert(cert_path)
        x509_context = X509(
            server=Server(
                name="TestX509", url="https://x509.example.com", version="v0"
            ),
            path=cert_path,
        )
        config = configuration_from_legacy_context("TestX509", x509_context)
        client = HTTPClient(config=config)
        hook_func = refresh(client)
        request = httpx.Request("GET", "/")

        hook_func(request)
        mock_refresh.assert_not_called()

    @patch("canfar.auth.oidc.sync_refresh")
    def test_skip_if_runtime_credentials_used(self, mock_refresh) -> None:
        """Verify the hook does nothing if runtime credentials are provided."""
        client = HTTPClient(token=SecretStr("runtime-token"), url="https://runtime.com")
        hook_func = refresh(client)
        request = httpx.Request("GET", "/")

        hook_func(request)
        mock_refresh.assert_not_called()

    @patch("canfar.auth.oidc.sync_refresh")
    def test_skip_if_token_not_expired(self, mock_refresh, oidc_client) -> None:
        """Verify the hook does nothing if the access token is not expired."""
        oidc_client.config.context.expiry.access = time.time() + 3600  # Make it valid
        hook_func = refresh(oidc_client)
        request = httpx.Request("GET", "/")

        hook_func(request)
        mock_refresh.assert_not_called()

    @patch("canfar.auth.oidc.sync_refresh", side_effect=Exception("Network Error"))
    def test_refresh_failure_raises_error(self, mock_refresh, oidc_client) -> None:  # noqa: ARG002
        """Verify that a failure during refresh raises AuthenticationError."""
        hook_func = refresh(oidc_client)
        request = httpx.Request("GET", "/")

        with pytest.raises(AuthenticationError, match="Failed to refresh OIDC token"):
            hook_func(request)


class TestAsyncHook:
    """Tests for the asynchronous `ahook` function."""

    @patch("canfar.models.config.Configuration.save")
    @patch("canfar.utils.jwt.expiry", return_value=time.time() + 3600)
    @patch("canfar.auth.oidc.refresh", return_value=SecretStr("new-async-token"))
    async def test_successful_async_refresh(
        self,
        mock_refresh,
        mock_expiry,  # noqa: ARG002
        mock_save,
        oidc_client,
    ) -> None:
        """Verify a successful async token refresh updates state and headers."""
        hook_func = arefresh(oidc_client)
        request = httpx.Request("GET", "https://oidc.example.com")

        await hook_func(request)

        mock_refresh.assert_called_once()
        mock_save.assert_called_once()

        assert request.headers["Authorization"] == "Bearer new-async-token"
        assert (
            oidc_client.asynclient.headers["Authorization"] == "Bearer new-async-token"
        )

        new_context = oidc_client.config.context
        assert isinstance(new_context, OIDC)
        assert new_context.token.access is not None
        assert new_context.token.access.get_secret_value() == "new-async-token"

    @patch("canfar.auth.oidc.refresh")
    async def test_skip_if_not_oidc_context_async(self, mock_refresh, tmp_path) -> None:
        """Verify the async hook does nothing for non-OIDC contexts."""
        cert_path = tmp_path / "cert.pem"
        generate_cert(cert_path)
        x509_context = X509(
            server=Server(
                name="TestX509", url="https://x509.example.com", version="v0"
            ),
            path=cert_path,
        )
        config = configuration_from_legacy_context("TestX509", x509_context)
        client = HTTPClient(config=config)
        hook_func = arefresh(client)
        request = httpx.Request("GET", "/")

        await hook_func(request)
        mock_refresh.assert_not_called()

    @patch("canfar.auth.oidc.refresh", side_effect=Exception("Async Network Error"))
    async def test_async_refresh_failure_raises_error(
        self,
        mock_refresh,  # noqa: ARG002
        oidc_client,
    ) -> None:
        """Verify a failure during async refresh raises AuthenticationError."""
        hook_func = arefresh(oidc_client)
        request = httpx.Request("GET", "/")

        with pytest.raises(AuthenticationError, match="Failed to refresh OIDC token"):
            await hook_func(request)


class TestSyncAsyncParity:
    """Characterization tests: sync and async auth hooks share guard behavior."""

    @patch("canfar.auth.oidc.sync_refresh")
    @patch("canfar.auth.oidc.refresh")
    def test_refresh_and_arefresh_both_skip_non_oidc(
        self,
        mock_async_refresh,
        mock_sync_refresh,
        tmp_path,
    ) -> None:
        """Both refresh and arefresh skip when the Authentication Record is not OIDC."""
        cert_path = tmp_path / "cert.pem"
        generate_cert(cert_path)
        x509_context = X509(
            server=Server(
                name="TestX509", url="https://x509.example.com", version="v0"
            ),
            path=cert_path,
        )
        config = configuration_from_legacy_context("TestX509", x509_context)
        client = HTTPClient(config=config)
        request = httpx.Request("GET", "/")

        refresh(client)(request)
        mock_sync_refresh.assert_not_called()
        mock_async_refresh.assert_not_called()

    @patch("canfar.auth.oidc.sync_refresh")
    @patch("canfar.auth.oidc.refresh")
    def test_refresh_and_arefresh_both_skip_runtime_credentials(
        self,
        mock_async_refresh,
        mock_sync_refresh,
    ) -> None:
        """Both refresh and arefresh skip when runtime credentials are active."""
        client = HTTPClient(token=SecretStr("runtime-token"), url="https://runtime.com")
        request = httpx.Request("GET", "/")

        refresh(client)(request)
        mock_sync_refresh.assert_not_called()
        mock_async_refresh.assert_not_called()
