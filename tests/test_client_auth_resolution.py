"""Request contracts for HTTP Authentication and Server resolution."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx
import pytest
from pydantic import AnyHttpUrl, AnyUrl, SecretStr

from canfar.client import HTTPClient
from canfar.exceptions.context import AuthContextError, AuthExpiredError
from canfar.models.active import ActiveConfig
from canfar.models.auth import (
    Client,
    Endpoint,
    Expiry,
    OIDCCredential,
    Token,
    X509Credential,
)
from canfar.models.config import Configuration
from canfar.models.http import Server
from tests.test_auth_x509 import generate_cert

if TYPE_CHECKING:
    from pathlib import Path

_REFRESHED_TOKEN = "e30.eyJleHAiOjIwMDB9.e30"  # gitleaks:allow


def _server() -> Server:
    return Server(
        idp="test",
        name="platform",
        uri=AnyUrl("ivo://test.example/skaha"),
        url=AnyHttpUrl("https://platform.example"),
        version="v1",
    )


def _configuration(credential: OIDCCredential | X509Credential) -> Configuration:
    return Configuration(
        active=ActiveConfig(authentication="test", server="platform"),
        authentication={"test": credential},
        servers={"platform": _server()},
    )


class TestRequestAuthenticationResolution:
    """Request contracts for canonical Authentication and Server resolution."""

    def test_refreshable_record_without_access_refreshes_first_request(
        self,
        tmp_path: Path,
    ) -> None:
        """A refresh token can bootstrap the first Platform request."""
        now = 1_000.0
        refreshed_token = _REFRESHED_TOKEN
        config = _configuration(
            OIDCCredential(
                idp="test",
                endpoints=Endpoint(
                    discovery=(
                        "https://identity.example/.well-known/openid-configuration"
                    ),
                    token="https://identity.example/token",
                ),
                client=Client(identity="client", secret="client-secret"),
                token=Token(refresh="refresh-secret"),
                expiry=Expiry(access=None, refresh=2_000.0),
            )
        )
        platform_requests: list[httpx.Request] = []
        token_requests: list[httpx.Request] = []
        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )
        token_transport = httpx.MockTransport(
            lambda request: (
                token_requests.append(request)
                or httpx.Response(
                    200,
                    json={"access_token": refreshed_token},
                    request=request,
                )
            )
        )
        client_type = httpx.Client

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: client_type(
                    transport=platform_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.auth.oidc.httpx.Client",
                side_effect=lambda **kwargs: client_type(
                    transport=token_transport,
                    **kwargs,
                ),
            ),
            HTTPClient(config=config) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert len(token_requests) == 1
        assert [request.headers["Authorization"] for request in platform_requests] == [
            f"Bearer {refreshed_token}"
        ]

    def test_unusable_oidc_record_raises_typed_safe_error(self) -> None:
        """Incomplete saved OIDC state is typed and never reveals secrets."""
        config = _configuration(
            OIDCCredential(
                idp="test",
                client=Client(identity="client", secret="client-secret"),
                token=Token(refresh="refresh-secret"),
            )
        )

        with pytest.raises(AuthContextError) as exc_info:
            _ = HTTPClient(config=config).client

        message = str(exc_info.value)
        assert "client-secret" not in message
        assert "refresh-secret" not in message

    def test_non_file_x509_record_raises_typed_safe_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Invalid saved certificate paths use the Authentication error type."""
        config = _configuration(
            X509Credential(idp="test", path=tmp_path, expiry=9_999_999_999.0)
        )

        with pytest.raises(AuthContextError, match=r"X\.509 certificate"):
            _ = HTTPClient(config=config).client

    def test_runtime_token_request_ignores_unusable_saved_authentication(self) -> None:
        """A runtime token request does not resolve the saved Authentication."""
        config = Configuration(
            active=ActiveConfig(authentication="srcnet", server=None),
            authentication={"srcnet": OIDCCredential(idp="srcnet")},
            servers={},
        )
        requests: list[httpx.Request] = []
        transport = httpx.MockTransport(
            lambda request: (
                requests.append(request) or httpx.Response(200, request=request)
            )
        )
        sync_client = httpx.Client

        with (
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: sync_client(
                    transport=transport,
                    **kwargs,
                ),
            ),
            HTTPClient(
                config=config,
                token=SecretStr("runtime-token"),
                url="https://runtime.example/api",
            ) as client,
        ):
            response = client.client.get("probe")

        assert response.status_code == 200
        assert str(requests[0].url) == "https://runtime.example/api/probe"
        assert requests[0].headers["Authorization"] == "Bearer runtime-token"

    @pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
    @pytest.mark.parametrize(
        "authentication",
        ["anonymous", "saved-oidc", "saved-x509", "runtime-token", "runtime-x509"],
    )
    async def test_request_authentication_matrix(
        self,
        authentication: str,
        asynchronous: bool,
        tmp_path: Path,
    ) -> None:
        """Sync and async requests apply the selected Authentication source."""
        cert_path = tmp_path / "client.pem"
        if authentication in {"saved-x509", "runtime-x509"}:
            generate_cert(cert_path)
        client_kwargs: dict[str, object] = {}
        expected_authorization: str | None = None
        expected_type: str | None = None

        if authentication == "saved-oidc":
            credential = OIDCCredential(
                idp="test",
                endpoints=Endpoint(
                    discovery=(
                        "https://identity.example/.well-known/openid-configuration"
                    ),
                    token="https://identity.example/token",
                ),
                client=Client(identity="client", secret="secret"),
                token=Token(access="saved-access", refresh="saved-refresh"),
                expiry=Expiry(access=9999999999.0, refresh=9999999999.0),
            )
            expected_authorization = "Bearer saved-access"
            expected_type = "OIDC"
        elif authentication == "saved-x509":
            credential = X509Credential(
                idp="test",
                path=cert_path,
                expiry=9999999999.0,
            )
            expected_type = "X509"
        else:
            credential = X509Credential(idp="test", path=None)

        config = _configuration(credential)
        if authentication == "runtime-token":
            client_kwargs = {
                "token": SecretStr("runtime-access"),
                "url": "https://runtime.example",
            }
            expected_authorization = "Bearer runtime-access"
            expected_type = "RUNTIME-TOKEN"
        elif authentication == "runtime-x509":
            client_kwargs = {
                "certificate": cert_path,
                "url": "https://runtime.example",
            }
            expected_type = "RUNTIME-X509"

        requests: list[httpx.Request] = []
        transport = httpx.MockTransport(
            lambda request: (
                requests.append(request) or httpx.Response(200, request=request)
            )
        )
        sync_client = httpx.Client
        async_client = httpx.AsyncClient

        with (
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: sync_client(
                    transport=transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.client.AsyncClient",
                side_effect=lambda **kwargs: async_client(
                    transport=transport,
                    **kwargs,
                ),
            ),
        ):
            if asynchronous:
                async with HTTPClient(config=config, **client_kwargs) as client:
                    response = await client.asynclient.get("probe")
            else:
                with HTTPClient(config=config, **client_kwargs) as client:
                    response = client.client.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        assert requests[0].headers.get("Authorization") == expected_authorization
        assert requests[0].headers.get("X-Skaha-Authentication-Type") == expected_type

    async def test_concurrent_requests_share_one_oidc_refresh(
        self,
        tmp_path: Path,
    ) -> None:
        """Concurrent async requests perform one refresh and use its token."""
        now = 1_000.0
        refreshed_token = _REFRESHED_TOKEN
        config = _configuration(
            OIDCCredential(
                idp="test",
                endpoints=Endpoint(
                    discovery=(
                        "https://identity.example/.well-known/openid-configuration"
                    ),
                    token="https://identity.example/token",
                ),
                client=Client(identity="client", secret="secret"),
                token=Token(access="expired", refresh="refresh"),
                expiry=Expiry(access=now - 1, refresh=now + 1_000),
            )
        )
        token_requests: list[httpx.Request] = []
        platform_requests: list[httpx.Request] = []

        async def refresh_token(request: httpx.Request) -> httpx.Response:
            token_requests.append(request)
            await asyncio.sleep(0.01)
            return httpx.Response(
                200,
                json={"access_token": refreshed_token},
                request=request,
            )

        token_transport = httpx.MockTransport(refresh_token)
        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )
        async_client = httpx.AsyncClient

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch(
                "canfar.client.AsyncClient",
                side_effect=lambda **kwargs: async_client(
                    transport=platform_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.auth.oidc.httpx.AsyncClient",
                side_effect=lambda **kwargs: async_client(
                    transport=token_transport,
                    **kwargs,
                ),
            ),
        ):
            async with HTTPClient(config=config) as client:
                responses = await asyncio.gather(
                    client.asynclient.get("one"),
                    client.asynclient.get("two"),
                )

        assert [response.status_code for response in responses] == [200, 200]
        assert len(token_requests) == 1
        assert [request.headers["Authorization"] for request in platform_requests] == [
            f"Bearer {refreshed_token}",
            f"Bearer {refreshed_token}",
        ]

    async def test_async_refresh_repairs_existing_sync_client(
        self,
        tmp_path: Path,
    ) -> None:
        """A sync request reads a token refreshed by the async client."""
        now = 1_000.0
        refreshed_token = _REFRESHED_TOKEN
        config = _configuration(
            OIDCCredential(
                idp="test",
                endpoints=Endpoint(
                    discovery=(
                        "https://identity.example/.well-known/openid-configuration"
                    ),
                    token="https://identity.example/token",
                ),
                client=Client(identity="client", secret="secret"),
                token=Token(access="expired", refresh="refresh"),
                expiry=Expiry(access=now - 1, refresh=now + 1_000),
            )
        )
        platform_requests: list[httpx.Request] = []
        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )
        token_transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"access_token": refreshed_token},
                request=request,
            )
        )
        sync_client = httpx.Client
        async_client = httpx.AsyncClient

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: sync_client(
                    transport=platform_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.client.AsyncClient",
                side_effect=lambda **kwargs: async_client(
                    transport=platform_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.auth.oidc.httpx.AsyncClient",
                side_effect=lambda **kwargs: async_client(
                    transport=token_transport,
                    **kwargs,
                ),
            ),
            HTTPClient(config=config) as client,
        ):
            async with client:
                sync = client.client
                async_response = await client.asynclient.get("refresh")
                sync_response = sync.get("after-refresh")

        assert [async_response.status_code, sync_response.status_code] == [200, 200]
        assert [request.headers["Authorization"] for request in platform_requests] == [
            f"Bearer {refreshed_token}",
            f"Bearer {refreshed_token}",
        ]

    @pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
    @pytest.mark.parametrize(
        ("state", "access_expiry", "refresh_expiry", "refreshes", "succeeds"),
        [
            ("valid", 1_100.0, 2_000.0, 0, True),
            ("expired", 900.0, 900.0, 0, False),
            ("refresh-eligible", 900.0, 2_000.0, 1, True),
            ("unrefreshable", 900.0, 2_000.0, 0, False),
        ],
    )
    async def test_refresh_and_expiry_outcome_matrix(
        self,
        state: str,
        access_expiry: float,
        refresh_expiry: float,
        refreshes: int,
        succeeds: bool,
        asynchronous: bool,
        tmp_path: Path,
    ) -> None:
        """The same Authentication Record has the same sync and async outcome."""
        now = 1_000.0
        refreshed_token = _REFRESHED_TOKEN
        config = _configuration(
            OIDCCredential(
                idp="test",
                endpoints=Endpoint(
                    discovery=(
                        "https://identity.example/.well-known/openid-configuration"
                    ),
                    token="https://identity.example/token",
                ),
                client=Client(identity="client", secret="secret"),
                token=Token(access="current-access", refresh="refresh"),
                expiry=Expiry(access=access_expiry, refresh=refresh_expiry),
            )
        )
        token_requests: list[httpx.Request] = []
        platform_requests: list[httpx.Request] = []

        def token(request: httpx.Request) -> httpx.Response:
            token_requests.append(request)
            return httpx.Response(
                200,
                json={"access_token": refreshed_token},
                request=request,
            )

        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )
        token_transport = httpx.MockTransport(token)
        sync_client = httpx.Client
        async_client = httpx.AsyncClient

        def make_unrefreshable() -> None:
            credential = config.get_credential("test")
            assert isinstance(credential, OIDCCredential)
            config.update_credential(
                credential.model_copy(
                    update={
                        "endpoints": credential.endpoints.model_copy(
                            update={"discovery": None}
                        )
                    }
                )
            )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: sync_client(
                    transport=platform_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.client.AsyncClient",
                side_effect=lambda **kwargs: async_client(
                    transport=platform_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.auth.oidc.httpx.Client",
                side_effect=lambda **kwargs: sync_client(
                    transport=token_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.auth.oidc.httpx.AsyncClient",
                side_effect=lambda **kwargs: async_client(
                    transport=token_transport,
                    **kwargs,
                ),
            ),
        ):
            if asynchronous:
                async with HTTPClient(config=config) as client:
                    request_client = client.asynclient
                    if state == "unrefreshable":
                        make_unrefreshable()
                    if succeeds:
                        response = await request_client.get("probe")
                    else:
                        with pytest.raises(AuthExpiredError):
                            await request_client.get("probe")
            else:
                with HTTPClient(config=config) as client:
                    request_client = client.client
                    if state == "unrefreshable":
                        make_unrefreshable()
                    if succeeds:
                        response = request_client.get("probe")
                    else:
                        with pytest.raises(AuthExpiredError):
                            request_client.get("probe")

        assert len(token_requests) == refreshes
        assert len(platform_requests) == int(succeeds)
        if succeeds:
            assert response.status_code == 200
