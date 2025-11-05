"""Tests for the HTTPx expiry hooks."""

from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from canfar.auth import x509
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
        mock_client = Mock()
        mock_client.config.context.expired = False

        hook_func = check(mock_client)
        request = httpx.Request("GET", "https://example.com")

        hook_func(request)

    def test_check_with_expired_context(self) -> None:
        """Test check hook with expired context (covers line 36)."""
        mock_client = Mock()
        mock_client.config.context.expired = True
        mock_client.config.context.mode = "OIDC"

        hook_func = check(mock_client)
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError) as exc_info:
            hook_func(request)

        assert "Auth Context 'OIDC' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)

    def test_check_with_real_client_expired(self) -> None:
        """Test check hook with real HTTPClient that has expired context."""
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
            expiry={"access": 0, "refresh": 0},
        )
        config = Configuration(active="TestOIDC", contexts={"TestOIDC": oidc_context})
        client = HTTPClient(config=config)

        hook_func = check(client)
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError) as exc_info:
            hook_func(request)

        assert "Auth Context 'oidc' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)

    def test_check_converts_certificate_error(self) -> None:
        """Synchronous hook should surface certificate details when loading fails."""

        class Context:
            mode = "x509"

            @property
            def expired(self) -> bool:
                """Raise a certificate error."""
                msg = "detailed certificate issue"
                raise x509.CertificateError(msg)

        hook = check(SimpleNamespace(config=SimpleNamespace(context=Context())))
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError, match="detailed certificate issue"):
            hook(request)


class TestACheck:
    """Test the acheck function."""

    @pytest.mark.asyncio
    async def test_acheck_with_valid_context(self) -> None:
        """Test acheck hook with valid (non-expired) context."""
        mock_client = Mock()
        mock_client.config.context.expired = False

        hook_func = acheck(mock_client)
        request = httpx.Request("GET", "https://example.com")

        await hook_func(request)

    @pytest.mark.asyncio
    async def test_acheck_with_expired_context(self) -> None:
        """Test acheck hook with expired context (covers line 62)."""
        mock_client = Mock()
        mock_client.config.context.expired = True
        mock_client.config.context.mode = "X509"

        hook_func = acheck(mock_client)
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError) as exc_info:
            await hook_func(request)

        assert "Auth Context 'X509' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_acheck_with_real_client_expired(self) -> None:
        """Test acheck hook with real HTTPClient that has expired context."""
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
            expiry={"access": 0, "refresh": 0},
        )
        config = Configuration(active="TestOIDC", contexts={"TestOIDC": oidc_context})
        client = HTTPClient(config=config)

        hook_func = acheck(client)
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError) as exc_info:
            await hook_func(request)

        assert "Auth Context 'oidc' expired" in str(exc_info.value)
        assert "auth expired" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_acheck_converts_certificate_error(self) -> None:
        """Async hook should surface certificate details when loading fails."""

        class Context:
            mode = "x509"

            @property
            def expired(self) -> bool:
                """Raise a certificate error."""
                msg = "detailed certificate issue"
                raise x509.CertificateError(msg)

        hook = acheck(SimpleNamespace(config=SimpleNamespace(context=Context())))
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError, match="detailed certificate issue"):
            await hook(request)

    @pytest.mark.anyio
    async def test_acheck_raises_for_expired_context(self) -> None:
        """Async hook raises AuthExpiredError when context reports expired."""

        class Context:
            mode = "x509"

            @property
            def expired(self) -> bool:
                return True

        hook = acheck(SimpleNamespace(config=SimpleNamespace(context=Context())))
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError, match="auth expired"):
            await hook(request)
