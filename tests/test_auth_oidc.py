"""Comprehensive tests for the OIDC authentication module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from canfar.auth.oidc import (
    AuthPendingError,
    SlowDownError,
    _cancel_pending_tasks,
    _poll_token,
    _poll_with_backoff,
    authenticate,
    authflow,
    discover,
    refresh,
    register,
    sync_refresh,
)
from canfar.models.auth import OIDC, Client, Endpoint, Token


class TestDiscoverFunction:
    """Test the discover function."""

    @pytest.mark.asyncio
    async def test_discover_with_client(self) -> None:
        """Test discover function with provided client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "device_authorization_endpoint": "https://example.com/device",
            "token_endpoint": "https://example.com/token",
            "userinfo_endpoint": "https://example.com/userinfo",
        }
        mock_client.get.return_value = mock_response

        result = await discover(
            "https://example.com/.well-known/openid-configuration", mock_client
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
                "device_authorization_endpoint": "https://example.com/device",
                "token_endpoint": "https://example.com/token",
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await discover(
                "https://example.com/.well-known/openid-configuration"
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
                "https://example.com/.well-known/openid-configuration", mock_client
            )


class TestRegisterFunction:
    """Test the register function."""

    @pytest.mark.asyncio
    async def test_register_with_client(self) -> None:
        """Test register function with provided client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
        }
        mock_client.post.return_value = mock_response

        result = await register("https://example.com/register", mock_client)

        assert result["client_id"] == "test_client_id"
        assert result["client_secret"] == "test_client_secret"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://example.com/register"
        assert "client_name" in call_args[1]["json"]
        # Check that client_name starts with "Science Platform CLI @"
        client_name = call_args[1]["json"]["client_name"]
        assert client_name.startswith("Science Platform CLI @")

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


class TestPollTokenFunction:
    """Test the _poll_token function."""

    @pytest.mark.asyncio
    async def test_poll_token_success(self) -> None:
        """Test successful token polling."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_type": "Bearer",
        }
        mock_client.post.return_value = mock_response

        result = await _poll_token(
            "https://example.com/token",
            "client_id",
            "client_secret",
            "device_code",
            mock_client,
        )

        assert result["access_token"] == "test_access_token"
        assert result["refresh_token"] == "test_refresh_token"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_poll_token_auth_pending(self) -> None:
        """Test token polling with authorization pending."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "authorization_pending"}
        mock_client.post.return_value = mock_response

        with pytest.raises(AuthPendingError):
            await _poll_token(
                "https://example.com/token",
                "client_id",
                "client_secret",
                "device_code",
                mock_client,
            )

    @pytest.mark.asyncio
    async def test_poll_token_slow_down(self) -> None:
        """Test token polling with slow down error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "slow_down"}
        mock_client.post.return_value = mock_response

        with pytest.raises(SlowDownError):
            await _poll_token(
                "https://example.com/token",
                "client_id",
                "client_secret",
                "device_code",
                mock_client,
            )

    @pytest.mark.asyncio
    async def test_poll_token_unknown_error(self) -> None:
        """Test token polling with unknown error."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "invalid_grant"}
        mock_client.post.return_value = mock_response

        with pytest.raises(
            ValueError, match="Unknown error in polling for tokens: invalid_grant"
        ):
            await _poll_token(
                "https://example.com/token",
                "client_id",
                "client_secret",
                "device_code",
                mock_client,
            )


class TestCancelPendingTasks:
    """Test the _cancel_pending_tasks helper function."""

    @pytest.mark.asyncio
    async def test_cancel_pending_tasks(self) -> None:
        """Test cancelling pending tasks."""

        # Create real async tasks that we can cancel
        async def dummy_task() -> None:
            await asyncio.sleep(10)  # Long sleep to ensure cancellation

        task1 = asyncio.create_task(dummy_task())
        task2 = asyncio.create_task(dummy_task())

        pending_tasks = {task1, task2}

        # Should not raise any exceptions
        await _cancel_pending_tasks(pending_tasks)

        # Verify tasks were cancelled
        assert task1.cancelled()
        assert task2.cancelled()


class TestPollWithBackoff:
    """Test the _poll_with_backoff function."""

    @pytest.mark.asyncio
    async def test_poll_with_backoff_success(self) -> None:
        """Test successful polling with backoff."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch("canfar.auth.oidc._poll_token") as mock_poll:
            mock_poll.return_value = {"access_token": "test_token"}

            result = await _poll_with_backoff(
                "https://example.com/token",
                "client_id",
                "client_secret",
                "device_code",
                mock_client,
                5,  # initial_interval
                600,  # expires
            )

            assert result["access_token"] == "test_token"
            mock_poll.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_poll_with_backoff_timeout(self) -> None:
        """Test polling with backoff timeout."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with patch("canfar.auth.oidc._poll_token") as mock_poll:
            mock_poll.side_effect = AuthPendingError()
            with patch("time.time") as mock_time:
                # Simulate time progression to trigger timeout
                mock_time.side_effect = [
                    0,
                    0,
                    0,
                    700,
                ]  # Start, first check, second check, timeout

                with pytest.raises(TimeoutError, match="Device flow timed out"):
                    await _poll_with_backoff(
                        "https://example.com/token",
                        "client_id",
                        "client_secret",
                        "device_code",
                        mock_client,
                        5,  # initial_interval
                        600,  # expires
                    )

    @pytest.mark.asyncio
    async def test_poll_with_backoff_slow_down(self) -> None:
        """Test polling with backoff and slow down."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch("canfar.auth.oidc._poll_token") as mock_poll,
            patch("asyncio.sleep") as mock_sleep,
        ):
            # First call raises SlowDownError, second succeeds
            mock_poll.side_effect = [
                SlowDownError(),
                {"access_token": "test_token"},
            ]

            result = await _poll_with_backoff(
                "https://example.com/token",
                "client_id",
                "client_secret",
                "device_code",
                mock_client,
                5,  # initial_interval
                600,  # expires
            )

            assert result["access_token"] == "test_token"
            assert mock_poll.call_count == 2
            # Should have slept with increased interval due to slow down
            mock_sleep.assert_called()


class TestAuthflowFunction:
    """Test the authflow function."""

    @pytest.mark.asyncio
    async def test_authflow_with_client(self) -> None:
        """Test authflow function with provided client."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        # Mock the device authorization response
        device_response = MagicMock()
        device_response.json.return_value = {
            "verification_uri_complete": "https://example.com/device?code=ABC123",
            "expires_in": 600,
            "interval": 5,
            "device_code": "device_code_123",
        }
        mock_client.post.return_value = device_response

        with (
            patch("canfar.auth.oidc._poll_with_backoff") as mock_poll,
            patch("webbrowser.get") as mock_browser,
            patch("segno.make") as mock_qr,
            patch("rich.progress.Progress") as mock_progress,
        ):
            mock_poll.return_value = {"access_token": "test_token"}
            mock_browser.return_value.open = MagicMock()
            mock_qr.return_value.terminal = MagicMock()

            # Mock progress context manager
            mock_progress_instance = MagicMock()
            mock_progress.return_value.__enter__.return_value = mock_progress_instance
            mock_progress.return_value.__exit__.return_value = None

            result = await authflow(
                "https://example.com/device",
                "https://example.com/token",
                "client_id",
                "client_secret",
                mock_client,
            )

            assert result["access_token"] == "test_token"
            mock_client.post.assert_called_once()
            mock_browser.return_value.open.assert_called_once()

    @pytest.mark.asyncio
    async def test_authflow_without_client(self) -> None:
        """Test authflow function without provided client."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock the device authorization response
            device_response = MagicMock()
            device_response.json.return_value = {
                "verification_uri_complete": "https://example.com/device?code=ABC123",
                "expires_in": 600,
                "interval": 5,
                "device_code": "device_code_123",
            }
            mock_client.post.return_value = device_response

            with (
                patch("canfar.auth.oidc._poll_with_backoff") as mock_poll,
                patch("webbrowser.get") as mock_browser,
                patch("segno.make") as mock_qr,
                patch("rich.progress.Progress") as mock_progress,
            ):
                mock_poll.return_value = {"access_token": "test_token"}
                mock_browser.return_value.open = MagicMock()
                mock_qr.return_value.terminal = MagicMock()

                # Mock progress context manager
                mock_progress_instance = MagicMock()
                mock_progress.return_value.__enter__.return_value = (
                    mock_progress_instance
                )
                mock_progress.return_value.__exit__.return_value = None

                result = await authflow(
                    "https://example.com/device",
                    "https://example.com/token",
                    "client_id",
                    "client_secret",
                )

                assert result["access_token"] == "test_token"


class TestAuthenticateFunction:
    """Test the authenticate function."""

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

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock discovery response
            discovery_response = MagicMock()
            discovery_response.json.return_value = {
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

            with (
                patch("canfar.auth.oidc.authflow") as mock_authflow,
                patch("canfar.utils.jwt.expiry") as mock_jwt_decode,
            ):
                mock_authflow.return_value = {
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                }
                mock_jwt_decode.return_value = 1234567890

                # Should complete without errors and return updated config
                result = await authenticate(oidc_config)

                # Verify the flow was called correctly
                mock_authflow.assert_called_once()
                assert mock_client.get.call_count == 2  # discovery + userinfo
                assert mock_client.post.call_count == 1  # registration

                # Verify the result has updated tokens
                assert result.token.access == "test_access_token"
                assert result.token.refresh == "test_refresh_token"
                assert result.expiry.access == 1234567890
                assert result.expiry.refresh == 1234567890


class TestRefreshFunction:
    """Test the async refresh function."""

    @pytest.mark.asyncio
    async def test_refresh_success(self) -> None:
        """Test successful async token refresh."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "new_access_token"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            result = await refresh(
                url="https://example.com/token",
                identity="client_id",
                secret="client_secret",
                token="refresh_token",
            )

            assert result.get_secret_value() == "new_access_token"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_http_error(self) -> None:
        """Test async refresh with HTTP error (lines 179-182)."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=MagicMock()
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            with pytest.raises(ValueError, match="HTTP error while refreshing"):
                await refresh(
                    url="https://example.com/token",
                    identity="client_id",
                    secret="client_secret",
                    token="refresh_token",
                )

    @pytest.mark.asyncio
    async def test_refresh_key_error(self) -> None:
        """Test async refresh with missing access token in response (lines 183-186)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "invalid_grant"}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            with pytest.raises(ValueError, match="server response does not contain"):
                await refresh(
                    url="https://example.com/token",
                    identity="client_id",
                    secret="client_secret",
                    token="refresh_token",
                )

    @pytest.mark.asyncio
    async def test_refresh_general_exception(self) -> None:
        """Test async refresh with general exception (lines 187-190)."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Network error")

            with pytest.raises(ValueError, match="Failed to refresh OIDC access token"):
                await refresh(
                    url="https://example.com/token",
                    identity="client_id",
                    secret="client_secret",
                    token="refresh_token",
                )


class TestSyncRefreshFunction:
    """Test the sync refresh function."""

    def test_sync_refresh_success(self) -> None:
        """Test successful sync token refresh."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "new_access_token"}

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            result = sync_refresh(
                url="https://example.com/token",
                identity="client_id",
                secret="client_secret",
                token="refresh_token",
            )

            assert result.get_secret_value() == "new_access_token"
            mock_client.post.assert_called_once()

    def test_sync_refresh_http_error(self) -> None:
        """Test sync refresh with HTTP error (lines 232-235)."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=MagicMock()
        )

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            with pytest.raises(ValueError, match="HTTP error while refreshing"):
                sync_refresh(
                    url="https://example.com/token",
                    identity="client_id",
                    secret="client_secret",
                    token="refresh_token",
                )

    def test_sync_refresh_key_error(self) -> None:
        """Test sync refresh with missing access token in response (lines 236-239)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "invalid_grant"}

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_response

            with pytest.raises(ValueError, match="server response does not contain"):
                sync_refresh(
                    url="https://example.com/token",
                    identity="client_id",
                    secret="client_secret",
                    token="refresh_token",
                )

    def test_sync_refresh_general_exception(self) -> None:
        """Test sync refresh with general exception (lines 240-242)."""
        with patch("httpx.Client") as mock_client_class:
            mock_client_class.side_effect = Exception("Network error")

            with pytest.raises(ValueError, match="Failed to refresh OIDC access token"):
                sync_refresh(
                    url="https://example.com/token",
                    identity="client_id",
                    secret="client_secret",
                    token="refresh_token",
                )


class TestIntegration:
    """Integration tests for OIDC module."""

    @pytest.mark.asyncio
    async def test_full_flow_integration(self) -> None:
        """Test the complete OIDC flow integration."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock all HTTP responses
            discovery_resp = MagicMock()
            discovery_resp.json.return_value = {
                "device_authorization_endpoint": "https://example.com/device",
                "registration_endpoint": "https://example.com/register",
                "token_endpoint": "https://example.com/token",
                "userinfo_endpoint": "https://example.com/userinfo",
            }

            registration_resp = MagicMock()
            registration_resp.json.return_value = {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            }

            device_auth_resp = MagicMock()
            device_auth_resp.json.return_value = {
                "verification_uri_complete": "https://example.com/device?code=ABC123",
                "expires_in": 600,
                "interval": 5,
                "device_code": "device_code_123",
            }

            token_resp = MagicMock()
            token_resp.json.return_value = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "token_type": "Bearer",
            }

            userinfo_resp = MagicMock()
            userinfo_resp.json.return_value = {
                "sub": "user123",
                "name": "Test User",
                "email": "test@example.com",
            }

            # Configure responses
            mock_client.get.side_effect = [
                discovery_resp,
                userinfo_resp,
            ]  # discovery, userinfo
            mock_client.post.side_effect = [
                registration_resp,
                device_auth_resp,
                token_resp,
            ]  # register, device auth, token

            # Mock UI components
            with (
                patch("webbrowser.get") as mock_browser,
                patch("segno.make") as mock_qr,
                patch("rich.progress.Progress") as mock_progress,
                patch("asyncio.sleep"),  # Speed up the test
            ):
                mock_browser.return_value.open = MagicMock()
                mock_qr.return_value.terminal = MagicMock()

                # Mock progress context manager
                mock_progress_instance = MagicMock()
                mock_progress.return_value.__enter__.return_value = (
                    mock_progress_instance
                )
                mock_progress.return_value.__exit__.return_value = None

                # Test the complete flow
                config = await discover(
                    "https://example.com/.well-known/openid-configuration",
                    mock_client,
                )
                client_info = await register(
                    config["registration_endpoint"], mock_client
                )

                # For the authflow, mock the polling to succeed immediately
                with patch("canfar.auth.oidc._poll_token") as mock_poll_token:
                    mock_poll_token.return_value = {
                        "access_token": "test_access_token",
                        "refresh_token": "test_refresh_token",
                    }

                    tokens = await authflow(
                        config["device_authorization_endpoint"],
                        config["token_endpoint"],
                        client_info["client_id"],
                        client_info["client_secret"],
                        mock_client,
                    )

                # Verify results
                assert (
                    config["device_authorization_endpoint"]
                    == "https://example.com/device"
                )
                assert client_info["client_id"] == "test_client_id"
                assert tokens["access_token"] == "test_access_token"
