"""Comprehensive tests for the OIDC authentication module."""

from __future__ import annotations

import base64
import logging
import time
from unittest.mock import AsyncMock, MagicMock, call, patch
from urllib.parse import parse_qs

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client, OAuth2Client

from canfar.auth.oidc import (
    authenticate,
    authflow,
    discover,
    poll_device_token,
    refresh,
    register,
    start_device_authorization,
    sync_refresh,
)
from canfar.models.auth import (
    OIDC,
    Client,
    DeviceAuthorization,
    Endpoint,
    Token,
)


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
    async def test_discover_without_client(self) -> None:
        """Test discover function without provided client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "issuer": "https://example.com",
                "device_authorization_endpoint": "https://example.com/device",
                "registration_endpoint": "https://example.com/register",
                "token_endpoint": "https://example.com/token",
                "userinfo_endpoint": "https://example.com/userinfo",
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await discover(
                "https://example.com/.well-known/openid-configuration",
                expected_issuer="https://example.com",
            )

            assert (
                result["device_authorization_endpoint"] == "https://example.com/device"
            )
            mock_client.get.assert_called_once()

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

    @pytest.mark.asyncio
    async def test_register_without_client(self) -> None:
        """Test register function without provided client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await register("https://example.com/register")

            assert result["client_id"] == "test_client_id"
            mock_client.post.assert_called_once()


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
                "client_id",
                "client_secret",
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
                    "client_id",
                    "client_secret",
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
                    "client_id",
                    "client_secret",
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
                    "client_id",
                    "client_secret",
                    challenge,
                    client,
                )

        sleep.assert_awaited_once_with(10)
        assert tokens["access_token"] == "test_access_token"

    @pytest.mark.asyncio
    async def test_poll_device_token_stops_when_access_is_denied(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """User denial is a safe terminal error and is never retried."""
        sentinel = "secret-error-description"
        client, requests = _oauth_client(
            httpx.Response(
                400,
                json={"error": "access_denied", "error_description": sentinel},
            )
        )
        challenge = _challenge(device_code="secret-device-code")

        async with client:
            with pytest.raises(
                PermissionError, match="authorization was denied"
            ) as exc:
                await poll_device_token(
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                    challenge,
                    client,
                )

        assert "secret-device-code" not in str(exc.value)
        assert sentinel not in str(exc.value)
        assert sentinel not in caplog.text
        assert len(requests) == 1

    @pytest.mark.asyncio
    async def test_poll_device_token_stops_when_challenge_expires(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Provider-reported expiration is an immediate terminal timeout."""
        sentinel = "secret-error-description"
        client, requests = _oauth_client(
            httpx.Response(
                400,
                json={"error": "expired_token", "error_description": sentinel},
            )
        )
        challenge = _challenge()

        async with client:
            with pytest.raises(TimeoutError, match="authorization expired") as exc:
                await poll_device_token(
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                    challenge,
                    client,
                )

        assert sentinel not in str(exc.value)
        assert sentinel not in caplog.text
        assert len(requests) == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("payload", "message"),
        [
            ({}, "malformed token response"),
            (
                {
                    "error": "invalid_grant",
                    "error_description": "secret-error-description",
                },
                "OIDC device authorization failed$",
            ),
        ],
    )
    async def test_poll_device_token_stops_on_other_terminal_errors(
        self,
        payload: dict[str, str],
        message: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Other OAuth failures stop immediately without leaking credentials."""
        client, requests = _oauth_client(httpx.Response(400, json=payload))
        challenge = _challenge(device_code="secret-device-code")

        async with client:
            with pytest.raises(ValueError, match=message) as exc:
                await poll_device_token(
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                    challenge,
                    client,
                )

        assert "secret-device-code" not in str(exc.value)
        assert "secret-error-description" not in str(exc.value)
        assert "secret-error-description" not in caplog.text
        assert len(requests) == 1

    @pytest.mark.asyncio
    async def test_poll_device_token_hides_server_error_response(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Token endpoint server errors become one safe terminal failure."""
        sentinel = "secret-server-response-body"
        client, requests = _oauth_client(httpx.Response(500, content=sentinel))
        challenge = _challenge(device_code="secret-device-code")

        async with client:
            with pytest.raises(
                ValueError, match=r"OIDC device authorization failed$"
            ) as exc:
                await poll_device_token(
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                    challenge,
                    client,
                )

        assert sentinel not in str(exc.value)
        assert sentinel not in caplog.text
        assert len(requests) == 1

    @pytest.mark.asyncio
    async def test_poll_device_token_hides_invalid_json_response(self) -> None:
        """Invalid token-response JSON becomes one safe terminal error."""
        client, _ = _oauth_client(
            httpx.Response(
                400,
                content=b"secret response body",
                headers={"content-type": "application/json"},
            )
        )
        challenge = _challenge()

        async with client:
            with pytest.raises(ValueError, match="malformed token response") as exc:
                await poll_device_token(
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                    challenge,
                    client,
                )

        assert "secret response body" not in str(exc.value)

    @pytest.mark.asyncio
    async def test_poll_device_token_rejects_nonobject_json_response(self) -> None:
        """A non-object token response is the same safe malformed failure."""
        client, _ = _oauth_client(httpx.Response(400, json=["secret response body"]))
        challenge = _challenge()

        async with client:
            with pytest.raises(ValueError, match="malformed token response") as exc:
                await poll_device_token(
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                    challenge,
                    client,
                )

        assert "secret response body" not in str(exc.value)

    @pytest.mark.asyncio
    async def test_authflow_without_client(self) -> None:
        """Test authflow function without provided client."""
        with patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client"
        ) as mock_client_class:
            mock_client = AsyncMock(spec=AsyncOAuth2Client)
            mock_client.fetch_token = AsyncMock(
                return_value={"access_token": "test_token"}
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock the device authorization response
            device_response = MagicMock()
            device_response.json.return_value = {
                "verification_uri": "https://example.com/device",
                "verification_uri_complete": "https://example.com/device?code=ABC123",
                "user_code": "ABC123",
                "expires_in": 600,
                "interval": 5,
                "device_code": "device_code_123",
            }
            mock_client.post.return_value = device_response

            result = await authflow(
                "https://example.com/device",
                "https://example.com/token",
                "client_id",
                "client_secret",
            )

            assert result["access_token"] == "test_token"


class TestAuthenticateFunction:
    """Test the authenticate function."""

    async def _authenticate_with_tokens(
        self,
        tokens: dict[str, object],
        *,
        oidc_config: OIDC | None = None,
        userinfo_error: Exception | None = None,
    ) -> OIDC:
        oidc_config = oidc_config or OIDC(
            endpoints=Endpoint(
                discovery="https://example.com/.well-known/openid-configuration"
            ),
            client=Client(),
            token=Token(),
        )

        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch(
                "authlib.integrations.httpx_client.AsyncOAuth2Client"
            ) as oauth_client_class,
        ):
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            oauth_client_class.return_value.__aenter__.return_value = AsyncMock(
                spec=AsyncOAuth2Client
            )

            discovery_response = MagicMock()
            discovery_response.json.return_value = {
                "issuer": "https://example.com",
                "device_authorization_endpoint": "https://example.com/device",
                "registration_endpoint": "https://example.com/register",
                "token_endpoint": "https://example.com/token",
                "userinfo_endpoint": "https://example.com/userinfo",
            }
            registration_response = MagicMock()
            registration_response.json.return_value = {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }
            userinfo_response = MagicMock()
            userinfo_response.json.return_value = {"preferred_username": "testuser"}
            userinfo_response.raise_for_status.side_effect = userinfo_error
            mock_client.get.side_effect = [discovery_response, userinfo_response]
            mock_client.post.return_value = registration_response

            return await authenticate(
                oidc_config,
                expected_issuer="https://example.com",
                device_flow=AsyncMock(return_value=tokens),
            )

    @pytest.mark.asyncio
    async def test_authenticate_preserves_issued_tokens_when_userinfo_fails(
        self,
    ) -> None:
        """A failed legacy UserInfo request retains the newly issued token state."""
        oidc_config = OIDC(
            endpoints=Endpoint(
                discovery="https://example.com/.well-known/openid-configuration"
            ),
            client=Client(),
            token=Token(access="old-access", refresh="old-refresh"),
            expiry={"access": 1, "refresh": 2},
        )
        endpoints = oidc_config.endpoints
        client = oidc_config.client
        userinfo_error = httpx.HTTPStatusError(
            "userinfo failed",
            request=httpx.Request("GET", "https://example.com/userinfo"),
            response=httpx.Response(500),
        )

        with pytest.raises(httpx.HTTPStatusError):
            await self._authenticate_with_tokens(
                {
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_at": 1893456000,
                },
                oidc_config=oidc_config,
                userinfo_error=userinfo_error,
            )

        assert oidc_config.endpoints is endpoints
        assert oidc_config.client is client
        assert oidc_config.token.access is not None
        assert oidc_config.token.access.get_secret_value() == "new-access"
        assert oidc_config.token.refresh is not None
        assert oidc_config.token.refresh.get_secret_value() == "new-refresh"
        assert oidc_config.expiry.access == 1893456000
        assert oidc_config.expiry.refresh is None

    @pytest.mark.asyncio
    async def test_authenticate_function(self) -> None:
        """Test the authenticate function integration."""
        # Create initial OIDC config
        oidc_config = OIDC(
            endpoints=Endpoint(
                discovery="https://example.com/.well-known/openid-configuration"
            ),
            client=Client(),
            token=Token(),
        )

        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch(
                "authlib.integrations.httpx_client.AsyncOAuth2Client"
            ) as oauth_client_class,
        ):
            mock_client = AsyncMock()
            oauth_client = AsyncMock(spec=AsyncOAuth2Client)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            oauth_client_class.return_value.__aenter__.return_value = oauth_client

            # Mock discovery response
            discovery_response = MagicMock()
            discovery_response.json.return_value = {
                "issuer": "https://example.com",
                "device_authorization_endpoint": "https://example.com/device",
                "registration_endpoint": "https://example.com/register",
                "token_endpoint": "https://example.com/token",
                "userinfo_endpoint": "https://example.com/userinfo",
            }

            # Mock registration response
            register_response = MagicMock()
            register_response.json.return_value = {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }

            # Mock userinfo response
            userinfo_response = MagicMock()
            userinfo_response.json.return_value = {
                "sub": "user123",
                "name": "Test User",
                "email": "test@example.com",
                "preferred_username": "testuser",
            }

            # Configure mock client responses
            mock_client.get.side_effect = [discovery_response, userinfo_response]
            mock_client.post.side_effect = [register_response]

            with patch("canfar.auth.oidc.authflow") as mock_authflow:
                mock_authflow.return_value = {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_at": 1234567890,
                }

                # Should complete without errors and return updated config
                result = await authenticate(
                    oidc_config,
                    expected_issuer="https://example.com",
                )

                # Verify the flow was called correctly
                assert result is oidc_config
                mock_authflow.assert_called_once()
                assert mock_client.get.call_count == 2  # discovery + userinfo
                assert mock_client.post.call_count == 1  # registration

                # Verify the result has updated tokens
                assert result.token.access is not None
                assert result.token.access.get_secret_value() == "test_access_token"
                assert result.token.refresh is not None
                assert result.token.refresh.get_secret_value() == "test_refresh_token"
                assert result.token.token_type == "Bearer"
                assert result.token.scope == "openid profile"
                assert result.expiry.access == 1234567890
                assert result.expiry.refresh is None

    @pytest.mark.asyncio
    async def test_authenticate_accepts_token_without_refresh_token(self) -> None:
        """Authentication succeeds when the token response omits a refresh token."""
        result = await self._authenticate_with_tokens(
            {
                "access_token": "test_access_token",
                "token_type": "Bearer",
                "scope": "openid profile",
                "expires_at": 1234567890,
            }
        )

        assert result.token.access is not None
        assert result.token.access.get_secret_value() == "test_access_token"
        assert result.token.refresh is None
        assert result.token.token_type == "Bearer"
        assert result.token.scope == "openid profile"
        assert result.expiry.access == 1234567890
        assert result.expiry.refresh is None

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "malformed_metadata",
        [
            {"token_type": ["secret-malformed-token-metadata"]},
            {"expires_at": "secret-malformed-token-metadata"},
        ],
        ids=["token-type", "access-expiry"],
    )
    async def test_authenticate_hides_malformed_token_metadata(
        self,
        malformed_metadata: dict[str, object],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Malformed token metadata becomes one safe Authentication failure."""
        sentinel = "secret-malformed-token-metadata"
        tokens: dict[str, object] = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
            "scope": "openid profile",
            "expires_at": 1234567890,
            **malformed_metadata,
        }

        with pytest.raises(
            ValueError,
            match=r"OIDC device authorization failed: malformed token response$",
        ) as exc:
            await self._authenticate_with_tokens(tokens)

        assert sentinel not in str(exc.value)
        assert sentinel not in caplog.text


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
