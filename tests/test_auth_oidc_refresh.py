"""Tests for OIDC token refresh."""

from __future__ import annotations

import base64
from unittest.mock import patch
from urllib.parse import parse_qs

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client, OAuth2Client

from canfar.auth.oidc import refresh, sync_refresh

_REFRESH_FAILURE_CASES = (
    ("oauth", "OIDC token refresh failed"),
    ("http", "OIDC token refresh failed"),
    ("invalid-json", "OIDC token refresh failed: malformed token response"),
    ("empty-access", "OIDC token refresh failed: malformed token response"),
)
_REFRESH_FAILURE_SENTINEL = "secret-provider-diagnostic"


def _refresh_failure_response(
    failure: str,
    request: httpx.Request,
) -> httpx.Response:
    """Return one deterministic failed refresh response."""
    if failure == "oauth":
        return httpx.Response(
            400,
            json={
                "error": "invalid_grant",
                "error_description": _REFRESH_FAILURE_SENTINEL,
            },
            request=request,
        )
    if failure == "http":
        return httpx.Response(
            503,
            text=_REFRESH_FAILURE_SENTINEL,
            request=request,
        )
    if failure == "empty-access":
        return httpx.Response(
            200,
            json={
                "access_token": "",
                "refresh_token": _REFRESH_FAILURE_SENTINEL,
            },
            request=request,
        )
    return httpx.Response(
        200,
        content=_REFRESH_FAILURE_SENTINEL,
        headers={"Content-Type": "application/json"},
        request=request,
    )


def _assert_basic_refresh_request(request: httpx.Request) -> None:
    """Assert the client secret is sent only with HTTP Basic authentication."""
    assert request.headers["Authorization"] == (
        "Basic " + base64.b64encode(b"client-id:client-secret").decode()
    )
    assert parse_qs(request.content.decode()) == {
        "grant_type": ["refresh_token"],
        "refresh_token": ["old-refresh"],
    }


class TestRefreshFunction:
    """Test the async refresh function."""

    @pytest.mark.asyncio
    async def test_refresh_success(self) -> None:
        """Authlib refreshes asynchronously with Basic auth and complete metadata."""
        requests: list[httpx.Request] = []

        def token_endpoint(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "access_token": "new-access",
                    "refresh_token": "rotated-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 3600,
                },
                request=request,
            )

        oauth_client = AsyncOAuth2Client(
            "client-id",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(token_endpoint),
        )
        with (
            patch(
                "authlib.integrations.httpx_client.AsyncOAuth2Client",
                return_value=oauth_client,
            ),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=1_000),
        ):
            result = await refresh(
                url="https://example.com/token",
                identity="client-id",
                secret="client-secret",
                token="old-refresh",
            )

        assert result == {
            "access_token": "new-access",
            "refresh_token": "rotated-refresh",
            "token_type": "Bearer",
            "scope": "openid profile",
            "expires_in": 3600,
            "expires_at": 4_600,
        }
        assert len(requests) == 1
        _assert_basic_refresh_request(requests[0])

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("failure", "message"),
        _REFRESH_FAILURE_CASES,
    )
    async def test_refresh_failure_is_fixed_and_secret_safe(
        self,
        failure: str,
        message: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """OAuth, HTTP, and malformed failures expose one fixed safe error."""
        oauth_client = AsyncOAuth2Client(
            "client-id",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(
                lambda request: _refresh_failure_response(failure, request)
            ),
        )
        with (
            patch(
                "authlib.integrations.httpx_client.AsyncOAuth2Client",
                return_value=oauth_client,
            ),
            pytest.raises(
                ValueError,
                match=r"^OIDC token refresh failed",
            ) as exc_info,
        ):
            await refresh(
                url="https://example.com/token",
                identity="client-id",
                secret="client-secret",
                token="old-refresh",
            )

        assert str(exc_info.value) == message
        assert exc_info.value.__cause__ is None
        assert _REFRESH_FAILURE_SENTINEL not in str(exc_info.value)
        assert _REFRESH_FAILURE_SENTINEL not in caplog.text


class TestSyncRefreshFunction:
    """Test the sync refresh function."""

    def test_sync_refresh_success(self) -> None:
        """Authlib preserves an omitted refresh token in the sync response."""
        requests: list[httpx.Request] = []

        def token_endpoint(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "access_token": "new-access",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 60,
                },
                request=request,
            )

        oauth_client = OAuth2Client(
            "client-id",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(token_endpoint),
        )
        with (
            patch(
                "authlib.integrations.httpx_client.OAuth2Client",
                return_value=oauth_client,
            ),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=1_000),
        ):
            result = sync_refresh(
                url="https://example.com/token",
                identity="client-id",
                secret="client-secret",
                token="old-refresh",
            )

        assert result == {
            "access_token": "new-access",
            "refresh_token": "old-refresh",
            "token_type": "Bearer",
            "scope": "openid profile",
            "expires_in": 60,
            "expires_at": 1_060,
        }
        assert len(requests) == 1
        _assert_basic_refresh_request(requests[0])

    @pytest.mark.parametrize(
        ("failure", "message"),
        _REFRESH_FAILURE_CASES,
    )
    def test_sync_refresh_failure_is_fixed_and_secret_safe(
        self,
        failure: str,
        message: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """OAuth, HTTP, and malformed failures expose one fixed safe error."""
        oauth_client = OAuth2Client(
            "client-id",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(
                lambda request: _refresh_failure_response(failure, request)
            ),
        )
        with (
            patch(
                "authlib.integrations.httpx_client.OAuth2Client",
                return_value=oauth_client,
            ),
            pytest.raises(
                ValueError,
                match=r"^OIDC token refresh failed",
            ) as exc_info,
        ):
            sync_refresh(
                url="https://example.com/token",
                identity="client-id",
                secret="client-secret",
                token="old-refresh",
            )

        assert str(exc_info.value) == message
        assert exc_info.value.__cause__ is None
        assert _REFRESH_FAILURE_SENTINEL not in str(exc_info.value)
        assert _REFRESH_FAILURE_SENTINEL not in caplog.text
