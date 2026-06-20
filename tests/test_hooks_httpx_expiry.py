"""Tests for the HTTPx expiry hooks."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import httpx
import pytest
from pydantic import SecretStr

from canfar.auth import x509
from canfar.client import HTTPClient
from canfar.exceptions.context import AuthExpiredError
from canfar.hooks.httpx.expiry import acheck, check
from canfar.models.auth import OIDC, X509
from canfar.models.http import Server
from tests.helpers.config import configuration_from_legacy_context
from tests.test_auth_x509 import generate_cert


class TestCheck:
    """Test the check function."""

    def test_check_with_valid_context(self) -> None:
        """Test check hook with valid (non-expired) context."""
        mock_client = Mock()
        mock_client.uses_runtime_credentials = False
        mock_client.config.context.expired = False

        hook_func = check(mock_client)
        request = httpx.Request("GET", "https://example.com")

        hook_func(request)

    def test_check_with_expired_context(self) -> None:
        """Test check hook with expired context (covers line 36)."""
        mock_client = Mock()
        mock_client.uses_runtime_credentials = False
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
        config = configuration_from_legacy_context("TestOIDC", oidc_context)
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

        hook = check(
            SimpleNamespace(
                config=SimpleNamespace(context=Context()),
                uses_runtime_credentials=False,
            )
        )
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError, match="detailed certificate issue"):
            hook(request)

    def test_skip_if_runtime_credentials_used(self, tmp_path) -> None:
        """Expiry hook must not check saved config when runtime token is active."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        x509_context = X509(
            server=Server(
                name="TestX509", url="https://x509.example.com", version="v0"
            ),
            path=cert_path,
        )
        config = configuration_from_legacy_context("TestX509", x509_context)
        client = HTTPClient(
            config=config,
            token=SecretStr("runtime-token"),
            url="https://runtime.com",
        )
        hook_func = check(client)
        request = httpx.Request("GET", "/")

        hook_func(request)

    def test_raises_without_runtime_credentials(self, tmp_path) -> None:
        """Expiry hook still checks saved config when no runtime credentials."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        x509_context = X509(
            server=Server(
                name="TestX509", url="https://x509.example.com", version="v0"
            ),
            path=cert_path,
        )
        config = configuration_from_legacy_context("TestX509", x509_context)
        client = HTTPClient(config=config)
        hook_func = check(client)
        request = httpx.Request("GET", "/")

        with pytest.raises(AuthExpiredError):
            hook_func(request)


class TestACheck:
    """Test the acheck function."""

    @pytest.mark.asyncio
    async def test_acheck_with_valid_context(self) -> None:
        """Test acheck hook with valid (non-expired) context."""
        mock_client = Mock()
        mock_client.uses_runtime_credentials = False
        mock_client.config.context.expired = False

        hook_func = acheck(mock_client)
        request = httpx.Request("GET", "https://example.com")

        await hook_func(request)

    @pytest.mark.asyncio
    async def test_acheck_with_expired_context(self) -> None:
        """Test acheck hook with expired context (covers line 62)."""
        mock_client = Mock()
        mock_client.uses_runtime_credentials = False
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
        config = configuration_from_legacy_context("TestOIDC", oidc_context)
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

        hook = acheck(
            SimpleNamespace(
                config=SimpleNamespace(context=Context()),
                uses_runtime_credentials=False,
            )
        )
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

        hook = acheck(
            SimpleNamespace(
                config=SimpleNamespace(context=Context()),
                uses_runtime_credentials=False,
            )
        )
        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError, match="auth expired"):
            await hook(request)

    @pytest.mark.anyio
    async def test_skip_if_runtime_credentials_used(self, tmp_path) -> None:
        """Async expiry hook must not check saved config with runtime token."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        x509_context = X509(
            server=Server(
                name="TestX509", url="https://x509.example.com", version="v0"
            ),
            path=cert_path,
        )
        config = configuration_from_legacy_context("TestX509", x509_context)
        client = HTTPClient(
            config=config,
            token=SecretStr("runtime-token"),
            url="https://runtime.com",
        )
        hook_func = acheck(client)
        request = httpx.Request("GET", "/")

        await hook_func(request)

    @pytest.mark.anyio
    async def test_raises_without_runtime_credentials(self, tmp_path) -> None:
        """Async expiry hook still checks saved config without runtime credentials."""
        cert_path = tmp_path / "expired.pem"
        generate_cert(cert_path, expired=True)
        x509_context = X509(
            server=Server(
                name="TestX509", url="https://x509.example.com", version="v0"
            ),
            path=cert_path,
        )
        config = configuration_from_legacy_context("TestX509", x509_context)
        client = HTTPClient(config=config)
        hook_func = acheck(client)
        request = httpx.Request("GET", "/")

        with pytest.raises(AuthExpiredError):
            await hook_func(request)


class TestSyncAsyncParity:
    """Characterization tests: sync and async hooks must behave identically."""

    def test_check_and_acheck_share_no_state(self) -> None:
        """The check and acheck factories return independent callables."""
        mock_client = Mock()
        mock_client.uses_runtime_credentials = False
        mock_client.config.context.expired = False

        hook_sync = check(mock_client)
        hook_async = acheck(mock_client)
        assert hook_sync is not hook_async

    @pytest.mark.anyio
    async def test_acheck_and_check_raise_same_error_for_expired(self) -> None:
        """Async and sync hooks raise AuthExpiredError with identical message."""

        class Context:
            mode = "x509"

            @property
            def expired(self) -> bool:
                return True

        def _ns() -> Any:
            return SimpleNamespace(
                config=SimpleNamespace(context=Context()),
                uses_runtime_credentials=False,
            )

        request = httpx.Request("GET", "https://example.com")

        with pytest.raises(AuthExpiredError, match="auth expired") as sync_exc:
            check(_ns())(request)

        with pytest.raises(AuthExpiredError, match="auth expired") as async_exc:
            await acheck(_ns())(request)

        assert str(sync_exc.value) == str(async_exc.value)
