"""Comprehensive tests for the OIDC authentication module."""

from __future__ import annotations

import base64
import logging
import time
from unittest.mock import AsyncMock, MagicMock, call, patch
from urllib.parse import parse_qs

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client

from canfar.auth.oidc import (
    authflow,
    discover,
    poll_device_token,
    register,
    start_device_authorization,
)
from canfar.models.auth import DeviceAuthorization


def _challenge(
    *,
    expires_in: int = 60,
    interval: int = 5,
    device_code: str = "device_code_123",
) -> DeviceAuthorization:
    """Return the standard RFC 8628 challenge used by polling contracts."""
    return DeviceAuthorization(
        verification_uri="https://example.com/device",
        user_code="ABC123",
        expires_in=expires_in,
        interval=interval,
        device_code=device_code,
    )


def _oauth_client(
    *responses: httpx.Response | Exception,
) -> tuple[AsyncOAuth2Client, list[httpx.Request]]:
    """Return an Authlib client backed by deterministic token responses."""
    remaining = iter(responses)
    requests: list[httpx.Request] = []

    async def token_endpoint(request: httpx.Request) -> httpx.Response:
        """Return the next deterministic token response."""
        requests.append(request)
        response = next(remaining)
        if isinstance(response, Exception):
            raise response
        return response

    return (
        AsyncOAuth2Client(
            "client_id",
            "client_secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(token_endpoint),
        ),
        requests,
    )


class TestDiscoverFunction:
    """Test the discover function."""

    @pytest.mark.asyncio
    async def test_discover_rejects_nonexact_issuer(self) -> None:
        """Discovery issuer must exactly match the configured IDP issuer."""
        client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.json.return_value = {"issuer": "https://example.com/"}
        client.get.return_value = response

        with pytest.raises(ValueError, match="OIDC discovery issuer mismatch"):
            await discover(
                "https://example.com/.well-known/openid-configuration",
                client,
                expected_issuer="https://example.com",
            )

    @pytest.mark.asyncio
    async def test_discover_rejects_missing_required_endpoint(self) -> None:
        """Discovery fails safely when required CANFAR endpoints are absent."""
        client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.json.return_value = {
            "issuer": "https://example.com",
            "device_authorization_endpoint": "https://example.com/device",
            "registration_endpoint": "https://example.com/register",
            "token_endpoint": None,
            "userinfo_endpoint": "https://example.com/userinfo",
        }
        client.get.return_value = response

        with pytest.raises(ValueError, match="token_endpoint"):
            await discover(
                "https://example.com/.well-known/openid-configuration",
                client,
                expected_issuer="https://example.com",
            )

    @pytest.mark.asyncio
    async def test_discover_with_client(self) -> None:
        """Test discover function with provided client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "issuer": "https://example.com",
            "device_authorization_endpoint": "https://example.com/device",
            "registration_endpoint": "https://example.com/register",
            "token_endpoint": "https://example.com/token",
            "userinfo_endpoint": "https://example.com/userinfo",
        }
        mock_client.get.return_value = mock_response

        result = await discover(
            "https://example.com/.well-known/openid-configuration",
            mock_client,
            expected_issuer="https://example.com",
        )

        assert result["device_authorization_endpoint"] == "https://example.com/device"
        assert result["token_endpoint"] == "https://example.com/token"
        mock_client.get.assert_called_once_with(
            "https://example.com/.well-known/openid-configuration"
        )
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_http_error(self) -> None:
        """Test discover function with HTTP error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        )
        mock_client.get.return_value = mock_response

        with pytest.raises(httpx.HTTPStatusError):
            await discover(
                "https://example.com/.well-known/openid-configuration",
                mock_client,
                expected_issuer="https://example.com",
            )


class TestRegisterFunction:
    """Test the register function."""

    @pytest.mark.asyncio
    async def test_register_with_client(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Registration returns complete data without logging its secret."""
        sentinel = "registration-client-secret-sentinel"
        registered = {
            "client_id": "test-client-id",
            "client_secret": sentinel,
        }
        client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.json.return_value = registered
        client.post.return_value = response

        logger = logging.getLogger("canfar.auth.oidc")
        logger.addHandler(caplog.handler)
        try:
            caplog.set_level(logging.DEBUG, logger="canfar.auth.oidc")
            result = await register("https://identity.example/register", client)
        finally:
            logger.removeHandler(caplog.handler)

        assert result == registered
        call = client.post.await_args
        assert call.args == ("https://identity.example/register",)
        assert call.kwargs["json"]["client_name"].startswith("Science Platform CLI @")
        assert sentinel not in caplog.text
        assert "OIDC dynamic client registration succeeded." in caplog.messages


class TestAuthflowFunction:
    """Test the authflow function."""

    @pytest.mark.asyncio
    async def test_authflow_runs_without_interactive_ui(self) -> None:
        """Protocol-only device Authentication has no interactive side effects."""
        client, _ = _oauth_client(
            httpx.Response(
                200,
                json={
                    "verification_uri": "https://example.com/device",
                    "verification_uri_complete": (
                        "https://example.com/device?code=ABC123"
                    ),
                    "user_code": "ABC123",
                    "expires_in": 600,
                    "interval": 5,
                    "device_code": "device_code_123",
                },
            ),
            httpx.Response(
                200,
                json={
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                },
            ),
        )

        interactive_side_effect = AssertionError(
            "OIDC protocol invoked interactive presentation"
        )
        async with client:
            with (
                patch(
                    "canfar.utils.console.get_console",
                    side_effect=interactive_side_effect,
                ),
                patch("webbrowser.get", side_effect=interactive_side_effect),
                patch("segno.make", side_effect=interactive_side_effect),
            ):
                tokens = await authflow(
                    "https://example.com/device",
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                    client,
                )

        assert tokens["access_token"] == "test_access_token"

    @pytest.mark.asyncio
    async def test_start_device_authorization_returns_domain_challenge(self) -> None:
        """Device authorization returns typed domain data for presentation."""
        client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.json.return_value = {
            "verification_uri": "https://example.com/device",
            "verification_uri_complete": "https://example.com/device?code=ABC123",
            "user_code": "ABC123",
            "expires_in": 600,
            "interval": 5,
            "device_code": "device_code_123",
        }
        client.post.return_value = response

        challenge = await start_device_authorization(
            "https://example.com/device",
            "client_id",
            "client_secret",
            client,
        )

        assert challenge == DeviceAuthorization(
            verification_uri="https://example.com/device",
            verification_uri_complete="https://example.com/device?code=ABC123",
            user_code="ABC123",
            expires_in=600,
            interval=5,
            device_code="device_code_123",
        )

    @pytest.mark.asyncio
    async def test_start_device_authorization_accepts_required_rfc_fields(self) -> None:
        """Complete verification URI and interval remain optional per RFC 8628."""
        client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.json.return_value = {
            "verification_uri": "https://example.com/device",
            "user_code": "ABC123",
            "expires_in": 600,
            "device_code": "device_code_123",
        }
        client.post.return_value = response

        challenge = await start_device_authorization(
            "https://example.com/device",
            "client_id",
            "client_secret",
            client,
        )

        assert challenge.verification_uri == "https://example.com/device"
        assert challenge.verification_uri_complete is None
        assert challenge.user_code.get_secret_value() == "ABC123"
        assert challenge.interval == 5

    @pytest.mark.asyncio
    async def test_start_device_authorization_hides_malformed_secrets(self) -> None:
        """Malformed challenge errors never echo provider-issued secret values."""
        client = AsyncMock(spec=httpx.AsyncClient)
        response = MagicMock()
        response.json.return_value = {
            "user_code": "secret-user-code",
            "expires_in": 600,
            "device_code": "secret-device-code",
        }
        client.post.return_value = response

        with pytest.raises(
            ValueError,
            match="Invalid OIDC device authorization response",
        ) as exc:
            await start_device_authorization(
                "https://example.com/device",
                "client_id",
                "client_secret",
                client,
            )

        assert "secret-user-code" not in str(exc.value)
        assert "secret-device-code" not in str(exc.value)

    @pytest.mark.asyncio
    async def test_poll_device_token_completes_domain_challenge(self) -> None:
        """Authlib exchanges a typed challenge using client_secret_basic."""
        requests: list[httpx.Request] = []

        async def token_endpoint(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(
                200,
                json={
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 3600,
                },
            )

        challenge = _challenge(expires_in=600)
        before = time.time()

        async with AsyncOAuth2Client(
            "client_id",
            "client_secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(token_endpoint),
        ) as client:
            tokens = await poll_device_token(
                "https://example.com/token",
                challenge,
                client,
            )

        request = requests[0]
        form = parse_qs(request.content.decode())
        credentials = base64.b64encode(b"client_id:client_secret").decode()
        assert request.headers["Authorization"] == f"Basic {credentials}"
        assert "client_secret" not in form
        assert form["grant_type"] == ["urn:ietf:params:oauth:grant-type:device_code"]
        assert form["device_code"] == ["device_code_123"]
        assert tokens["refresh_token"] == "test_refresh_token"
        assert tokens["expires_at"] - before == pytest.approx(3600, abs=1)

    @pytest.mark.asyncio
    async def test_poll_device_token_adds_five_seconds_after_slow_down(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """RFC 8628 slow_down adds five seconds to all later polling intervals."""
        sentinel = "secret-error-description"
        client, _ = _oauth_client(
            httpx.Response(
                400,
                json={"error": "slow_down", "error_description": sentinel},
            ),
            httpx.Response(
                400,
                json={
                    "error": "authorization_pending",
                    "error_description": sentinel,
                },
            ),
            httpx.Response(200, json={"access_token": "test_access_token"}),
        )
        challenge = _challenge()

        async with client:
            with patch("asyncio.sleep", new_callable=AsyncMock) as sleep:
                tokens = await poll_device_token(
                    "https://example.com/token",
                    challenge,
                    client,
                )

        assert sleep.await_args_list == [call(10), call(10)]
        assert tokens["access_token"] == "test_access_token"
        assert sentinel not in caplog.text

    @pytest.mark.asyncio
    async def test_poll_device_token_stops_at_monotonic_deadline(self) -> None:
        """Pending authorization never polls beyond the challenge lifetime."""
        pending = httpx.Response(400, json={"error": "authorization_pending"})
        client, requests = _oauth_client(
            pending,
            httpx.Response(400, json={"error": "authorization_pending"}),
            httpx.Response(200, json={"access_token": "too-late"}),
        )
        challenge = _challenge(expires_in=6)
        clock = 0.0

        def monotonic() -> float:
            return clock

        async def advance(seconds: float) -> None:
            nonlocal clock
            clock += seconds

        async with client:
            with (
                patch("time.monotonic", side_effect=monotonic),
                patch("asyncio.sleep", side_effect=advance) as sleep,
                pytest.raises(TimeoutError, match="Device flow timed out"),
            ):
                await poll_device_token(
                    "https://example.com/token",
                    challenge,
                    client,
                )

        assert len(requests) == 2
        assert sleep.await_args_list == [call(5), call(1)]

    @pytest.mark.asyncio
    async def test_poll_device_token_backs_off_after_network_timeout(self) -> None:
        """Network timeouts reduce polling frequency before retrying."""
        client, _ = _oauth_client(
            httpx.ConnectTimeout("network timeout"),
            httpx.Response(200, json={"access_token": "test_access_token"}),
        )
        challenge = _challenge()

        async with client:
            with patch("asyncio.sleep", new_callable=AsyncMock) as sleep:
                tokens = await poll_device_token(
                    "https://example.com/token",
                    challenge,
                    client,
                )

        sleep.assert_awaited_once_with(10)
        assert tokens["access_token"] == "test_access_token"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("response", "error", "match", "device_code"),
        [
            (
                httpx.Response(
                    400,
                    json={
                        "error": "access_denied",
                        "error_description": "secret-error-description",
                    },
                ),
                PermissionError,
                "authorization was denied",
                "secret-device-code",
            ),
            (
                httpx.Response(
                    400,
                    json={
                        "error": "expired_token",
                        "error_description": "secret-error-description",
                    },
                ),
                TimeoutError,
                "authorization expired",
                "device_code_123",
            ),
            (
                httpx.Response(400, json={}),
                ValueError,
                "malformed token response",
                "secret-device-code",
            ),
            (
                httpx.Response(
                    400,
                    json={
                        "error": "invalid_grant",
                        "error_description": "secret-error-description",
                    },
                ),
                ValueError,
                r"OIDC device authorization failed$",
                "secret-device-code",
            ),
            (
                httpx.Response(500, content="secret-server-response-body"),
                ValueError,
                r"OIDC device authorization failed$",
                "secret-device-code",
            ),
            (
                httpx.Response(
                    400,
                    content=b"secret response body",
                    headers={"content-type": "application/json"},
                ),
                ValueError,
                "malformed token response",
                "device_code_123",
            ),
            (
                httpx.Response(400, json=["secret response body"]),
                ValueError,
                "malformed token response",
                "device_code_123",
            ),
        ],
        ids=[
            "access-denied",
            "expired-token",
            "empty-error",
            "invalid-grant",
            "server-error",
            "invalid-json",
            "nonobject-json",
        ],
    )
    async def test_poll_device_token_stops_on_terminal_errors(
        self,
        response: httpx.Response,
        error: type[BaseException],
        match: str,
        device_code: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Terminal OAuth/HTTP failures stop immediately without leaking secrets."""
        client, requests = _oauth_client(response)
        challenge = _challenge(device_code=device_code)

        async with client:
            with pytest.raises(error, match=match) as exc:
                await poll_device_token(
                    "https://example.com/token",
                    challenge,
                    client,
                )

        message = str(exc.value)
        assert "secret-device-code" not in message
        assert "secret-error-description" not in message
        assert "secret-server-response-body" not in message
        assert "secret response body" not in message
        assert "secret-error-description" not in caplog.text
        assert "secret-server-response-body" not in caplog.text
        assert len(requests) == 1
