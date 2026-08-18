"""Contract tests for the native synchronous OIDC device flow."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import httpx
import pytest
from authlib.integrations.httpx_client import OAuth2Client
from pydantic import SecretStr

from canfar.auth.oidc import sync_authenticate_credential, sync_poll_device_token
from canfar.models.auth import Client, DeviceAuthorization, Endpoint, OIDCCredential


def _challenge(
    *,
    expires_in: int = 60,
    interval: int = 5,
    device_code: str = "device_code_123",
) -> DeviceAuthorization:
    """Return a deterministic RFC 8628 challenge."""
    return DeviceAuthorization(
        verification_uri="https://example.com/device",
        user_code="ABC123",
        expires_in=expires_in,
        interval=interval,
        device_code=device_code,
    )


def _oauth_client(
    *responses: httpx.Response | Exception,
) -> tuple[OAuth2Client, list[httpx.Request]]:
    """Return an Authlib client backed by deterministic token responses."""
    remaining = iter(responses)
    requests: list[httpx.Request] = []

    def token_endpoint(request: httpx.Request) -> httpx.Response:
        """Return the next deterministic token response."""
        requests.append(request)
        response = next(remaining)
        if isinstance(response, Exception):
            raise response
        return response

    return (
        OAuth2Client(
            "client_id",
            "client_secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(token_endpoint),
        ),
        requests,
    )


def test_sync_poll_device_token_waits_at_protocol_interval() -> None:
    """A pending authorization waits before the next token request."""
    client, requests = _oauth_client(
        httpx.Response(400, json={"error": "authorization_pending"}),
        httpx.Response(200, json={"access_token": "access-token"}),
    )

    with client, patch("canfar.auth.oidc.time.sleep") as sleep:
        tokens = sync_poll_device_token(
            "https://example.com/token",
            _challenge(),
            client,
        )

    assert tokens["access_token"] == "access-token"
    assert len(requests) == 2
    assert sleep.call_args_list == [call(5)]


def test_sync_poll_device_token_expires_at_challenge_deadline() -> None:
    """Pending authorization stops at the challenge expiry deadline."""
    client, requests = _oauth_client(
        httpx.Response(400, json={"error": "authorization_pending"}),
        httpx.Response(400, json={"error": "authorization_pending"}),
        httpx.Response(200, json={"access_token": "too-late"}),
    )
    clock = 0.0

    def monotonic() -> float:
        return clock

    def advance(seconds: float) -> None:
        nonlocal clock
        clock += seconds

    with (
        client,
        patch("canfar.auth.oidc.time.monotonic", side_effect=monotonic),
        patch("canfar.auth.oidc.time.sleep", side_effect=advance) as sleep,
        pytest.raises(TimeoutError, match="Device flow timed out"),
    ):
        sync_poll_device_token(
            "https://example.com/token",
            _challenge(expires_in=6),
            client,
        )

    assert len(requests) == 2
    assert sleep.call_args_list == [call(5), call(1)]


def test_sync_poll_device_token_reports_denial_without_secrets() -> None:
    """Terminal denial omits OIDC Identity Provider response data."""
    client, requests = _oauth_client(
        httpx.Response(
            400,
            json={
                "error": "access_denied",
                "error_description": "secret-error-description",
            },
        )
    )

    with client, pytest.raises(PermissionError, match="authorization was denied"):
        sync_poll_device_token(
            "https://example.com/token",
            _challenge(device_code="secret-device-code"),
            client,
        )

    assert len(requests) == 1


def test_sync_poll_device_token_retries_transport_failure() -> None:
    """A transport failure backs off and retries before succeeding."""
    client, _ = _oauth_client(
        httpx.ConnectTimeout("network timeout"),
        httpx.Response(200, json={"access_token": "access-token"}),
    )

    with client, patch("canfar.auth.oidc.time.sleep") as sleep:
        tokens = sync_poll_device_token(
            "https://example.com/token",
            _challenge(),
            client,
        )

    assert tokens["access_token"] == "access-token"
    sleep.assert_called_once_with(10)


def test_sync_authenticate_credential_runs_complete_native_flow() -> None:
    """Sync authentication performs discovery, registration, device, and userinfo."""
    credential = OIDCCredential(
        idp="srcnet",
        endpoints=Endpoint(
            discovery="https://example.com/.well-known/openid-configuration"
        ),
        client=Client(),
    )
    discovery = httpx.Response(
        200,
        request=httpx.Request(
            "GET", "https://example.com/.well-known/openid-configuration"
        ),
        json={
            "issuer": "https://example.com",
            "device_authorization_endpoint": "https://example.com/device",
            "registration_endpoint": "https://example.com/register",
            "token_endpoint": "https://example.com/token",
            "userinfo_endpoint": "https://example.com/userinfo",
        },
    )
    registration = httpx.Response(
        200,
        request=httpx.Request("POST", "https://example.com/register"),
        json={"client_id": "client-id", "client_secret": "client-secret"},
    )
    challenge = httpx.Response(
        200,
        request=httpx.Request("POST", "https://example.com/device"),
        json={
            "verification_uri": "https://example.com/device",
            "user_code": "ABC123",
            "expires_in": 600,
            "interval": 5,
            "device_code": "device-code",
        },
    )
    userinfo = httpx.Response(
        200,
        request=httpx.Request("GET", "https://example.com/userinfo"),
        json={"preferred_username": "test-user"},
    )
    sync_client = MagicMock()
    sync_client.get.side_effect = [discovery, userinfo]
    sync_client.post.return_value = registration
    oauth_client = MagicMock()
    oauth_client.post.return_value = challenge
    oauth_client.fetch_token.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "Bearer",
        "scope": "openid profile",
        "expires_at": 1893456000,
    }
    presented: list[DeviceAuthorization] = []

    with (
        patch("canfar.auth.oidc.httpx.Client") as client_class,
        patch("authlib.integrations.httpx_client.OAuth2Client") as oauth_client_class,
        patch("canfar.auth.oidc.time.sleep"),
    ):
        client_class.return_value.__enter__.return_value = sync_client
        oauth_client_class.return_value.__enter__.return_value = oauth_client
        result = sync_authenticate_credential(
            credential,
            expected_issuer="https://example.com",
            on_challenge=presented.append,
        )

    assert result.client.identity == "client-id"
    assert result.client.secret == SecretStr("client-secret")
    assert result.token.access == SecretStr("access-token")
    assert result.token.refresh == SecretStr("refresh-token")
    assert presented[0].user_code == SecretStr("ABC123")
    sync_client.get.assert_any_call(
        "https://example.com/.well-known/openid-configuration"
    )
    sync_client.get.assert_any_call(
        "https://example.com/userinfo",
        headers={"Authorization": "Bearer access-token"},
    )
