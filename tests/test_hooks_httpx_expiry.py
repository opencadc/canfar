"""Tests for the HTTPx expiry hooks."""

from unittest.mock import Mock

import httpx
import pytest

from canfar.client import HTTPClient
from canfar.exceptions.context import AuthExpiredError
from canfar.hooks.httpx.expiry import acheck, check
from canfar.models.auth import OIDC
from canfar.models.config import Configuration
from canfar.models.http import Server


class TestCheck:
    """Test the check function."""

    def test_check_with_valid_context(self) -> None:
        """Test check hook with valid (non-expired) context."""
        # Create a mock client with non-expired context
        mock_client = Mock()
        mock_client.config.context.expired = False

        hook_func = check(mock_client)
        request = httpx.Request("GET", "https://example.com")

        # Should not raise any exception
        hook_func(request)

    def test_check_with_expired_context(self) -> None:
        """Test check hook with expired context (covers line 36)."""
        # Create a mock client with expired context
        mock_client = Mock()
        mock_client.config.context.expired = True
        mock_client.config.context.mode = "OIDC"

        hook_func = check(mock_client)
        request = httpx.Request("GET", "https://example.com")

        # Should raise AuthExpiredError
        with pytest.raises(AuthExpiredError) as exc_info:
            hook_func(request)

        # Check the error message contains the expected context and reason
        assert "Auth Context 'OIDC' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)

    def test_check_with_real_client_expired(self) -> None:
        """Test check hook with real HTTPClient that has expired context."""
        # Create a real OIDC context that is expired
        oidc_context = OIDC(
            server=Server(
                name="TestOIDC", url="https://oidc.example.com", version="v1"
            ),
            endpoints={
                "discovery": "https://oidc.example.com/.well-known/openid-configuration",
                "token": "https://oidc.example.com/token",
            },
            client={"identity": "test-client", "secret": "test-secret"},
            token={"access": "expired-token", "refresh": "expired-refresh-token"},
            expiry={"access": 0, "refresh": 0},  # Both expired
        )
        config = Configuration(active="TestOIDC", contexts={"TestOIDC": oidc_context})
        client = HTTPClient(config=config)

        hook_func = check(client)
        request = httpx.Request("GET", "https://example.com")

        # Should raise AuthExpiredError
        with pytest.raises(AuthExpiredError) as exc_info:
            hook_func(request)

        # Check the error message contains the expected context and reason
        assert "Auth Context 'oidc' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)


class TestACheck:
    """Test the acheck function."""

    @pytest.mark.asyncio
    async def test_acheck_with_valid_context(self) -> None:
        """Test acheck hook with valid (non-expired) context."""
        # Create a mock client with non-expired context
        mock_client = Mock()
        mock_client.config.context.expired = False

        hook_func = acheck(mock_client)
        request = httpx.Request("GET", "https://example.com")

        # Should not raise any exception
        await hook_func(request)

    @pytest.mark.asyncio
    async def test_acheck_with_expired_context(self) -> None:
        """Test acheck hook with expired context (covers line 62)."""
        # Create a mock client with expired context
        mock_client = Mock()
        mock_client.config.context.expired = True
        mock_client.config.context.mode = "X509"

        hook_func = acheck(mock_client)
        request = httpx.Request("GET", "https://example.com")

        # Should raise AuthExpiredError
        with pytest.raises(AuthExpiredError) as exc_info:
            await hook_func(request)

        # Check the error message contains the expected context and reason
        assert "Auth Context 'X509' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_acheck_with_real_client_expired(self) -> None:
        """Test acheck hook with real HTTPClient that has expired context."""
        # Create a real OIDC context that is expired
        oidc_context = OIDC(
            server=Server(
                name="TestOIDC", url="https://oidc.example.com", version="v1"
            ),
            endpoints={
                "discovery": "https://oidc.example.com/.well-known/openid-configuration",
                "token": "https://oidc.example.com/token",
            },
            client={"identity": "test-client", "secret": "test-secret"},
            token={"access": "expired-token", "refresh": "expired-refresh-token"},
            expiry={"access": 0, "refresh": 0},  # Both expired
        )
        config = Configuration(active="TestOIDC", contexts={"TestOIDC": oidc_context})
        client = HTTPClient(config=config)

        hook_func = acheck(client)
        request = httpx.Request("GET", "https://example.com")

        # Should raise AuthExpiredError
        with pytest.raises(AuthExpiredError) as exc_info:
            await hook_func(request)

        # Check the error message contains the expected context and reason
        assert "Auth Context 'oidc' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)
