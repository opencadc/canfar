"""Tests for OIDC authentication orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client

from canfar.auth.oidc import authenticate
from canfar.models.auth import OIDC, Client, Endpoint, Token


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
