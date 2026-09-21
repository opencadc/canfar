"""Request contracts for HTTP Authentication and Server resolution."""

from __future__ import annotations

import asyncio
from contextlib import ExitStack, nullcontext
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client, OAuth2Client
from pydantic import AnyHttpUrl, AnyUrl, SecretStr

from canfar.client import HTTPClient
from canfar.exceptions.context import (
    AuthContextError,
    AuthRequiredError,
)
from canfar.hooks.httpx.auth import AuthenticationError, arefresh
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
from canfar.sessions import AsyncSession
from tests.test_auth_x509 import generate_cert

if TYPE_CHECKING:
    from pathlib import Path

_REFRESHED_TOKEN = "opaque-refreshed-access-token"
_UNUSABLE_OIDC_SECRETS = (
    "selected-client-secret",
    "selected-refresh-secret",
)
_MISLEADING_FUTURE_JWT_ACCESS_TOKEN = (  # gitleaks:allow
    "e30.eyJleHAiOjk5OTk5OTk5OTl9.e30"
)


def _server() -> Server:
    """Build the platform server shared by authentication tests."""
    return Server(
        idp="test",
        name="platform",
        uri=AnyUrl("ivo://test.example/skaha"),
        url=AnyHttpUrl("https://platform.example"),
        version="v1",
    )


def _configuration(credential: OIDCCredential | X509Credential) -> Configuration:
    """Build an active configuration around the supplied credential."""
    return Configuration(
        active=ActiveConfig(authentication="test", server="platform"),
        authentication={"test": credential},
        servers={"platform": _server()},
    )


def _oidc(
    *,
    access: str | None = "access",
    refresh: str | None = "refresh",
    access_expiry: float | None = 9_999_999_999.0,
    refresh_expiry: float | None = 9_999_999_999.0,
    discovery: str | None = (
        "https://identity.example/.well-known/openid-configuration"
    ),
    secret_expiry: int | None = None,
) -> OIDCCredential:
    """Build one OIDC Authentication Record for resolution tests."""
    return OIDCCredential(
        idp="test",
        endpoints=Endpoint(
            discovery=discovery,
            token="https://identity.example/token",
        ),
        client=Client(
            identity="client", secret="secret", secret_expires_at=secret_expiry
        ),
        token=Token(
            access=access,
            refresh=refresh,
            token_type="Legacy",
            scope="openid",
        ),
        expiry=Expiry(access=access_expiry, refresh=refresh_expiry),
    )


def _enter_clients(
    stack: ExitStack,
    platform: httpx.BaseTransport,
    *,
    token: httpx.BaseTransport | None = None,
) -> None:
    """Enter sync/async platform clients and optional Authlib token clients."""
    sync = httpx.Client
    async_client = httpx.AsyncClient
    stack.enter_context(
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: sync(transport=platform, **kwargs),
        )
    )
    stack.enter_context(
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: async_client(transport=platform, **kwargs),
        )
    )
    if token is None:
        return
    stack.enter_context(
        patch(
            "authlib.integrations.httpx_client.OAuth2Client",
            side_effect=lambda *args, **kwargs: OAuth2Client(
                *args, transport=token, **kwargs
            ),
        )
    )
    stack.enter_context(
        patch(
            "authlib.integrations.httpx_client.AsyncOAuth2Client",
            side_effect=lambda *args, **kwargs: AsyncOAuth2Client(
                *args, transport=token, **kwargs
            ),
        )
    )


class TestRequestAuthenticationResolution:
    """Request contracts for canonical Authentication and Server resolution."""

    @pytest.mark.parametrize(
        ("token_response", "expected_token", "expected_expiry"),
        [
            (
                {
                    "access_token": _REFRESHED_TOKEN,
                    "refresh_token": "rotated-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 300,
                },
                Token(
                    access=_REFRESHED_TOKEN,
                    refresh="rotated-refresh",
                    token_type="Bearer",
                    scope="openid profile",
                ),
                Expiry(access=1_300.0, refresh=None),
            ),
            (
                {"access_token": _REFRESHED_TOKEN, "expires_in": 300},
                Token(
                    access=_REFRESHED_TOKEN,
                    refresh="refresh-secret",
                    token_type="Legacy",
                    scope="openid",
                ),
                Expiry(access=1_300.0, refresh=2_000.0),
            ),
        ],
        ids=["rotated", "optional-fields-omitted"],
    )
    def test_refreshable_record_without_access_refreshes_first_request(
        self,
        token_response: dict[str, object],
        expected_token: Token,
        expected_expiry: Expiry,
        tmp_path: Path,
    ) -> None:
        """Refresh metadata is atomically persisted or preserved when omitted."""
        now = 1_000.0
        config = _configuration(
            _oidc(
                access=None,
                refresh="refresh-secret",
                access_expiry=None,
                refresh_expiry=2_000.0,
            ).model_copy(
                update={"client": Client(identity="client", secret="client-secret")}
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
                or httpx.Response(200, json=token_response, request=request)
            )
        )
        oauth_client = OAuth2Client(
            "client",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=token_transport,
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: httpx.Client(
                    transport=platform_transport, **kwargs
                ),
            ),
            patch(
                "authlib.integrations.httpx_client.OAuth2Client",
                return_value=oauth_client,
            ),
            HTTPClient(config=config) as client,
        ):
            response = client.client.get("probe")
            persisted = Configuration().authentication["test"]

        assert response.status_code == 200
        assert len(token_requests) == 1
        assert [request.headers["Authorization"] for request in platform_requests] == [
            f"Bearer {_REFRESHED_TOKEN}"
        ]
        canonical = config.authentication["test"]
        assert isinstance(canonical, OIDCCredential)
        assert canonical == persisted
        assert canonical.token == expected_token
        assert canonical.expiry == expected_expiry

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

    def test_missing_x509_certificate_means_not_authenticated(
        self,
        tmp_path: Path,
    ) -> None:
        """A saved record whose certificate was never issued asks for login."""
        config = _configuration(
            X509Credential(idp="test", path=tmp_path / "absent.pem", expiry=0.0)
        )

        with pytest.raises(AuthRequiredError, match="Not authenticated"):
            _ = HTTPClient(config=config).client

    @pytest.mark.parametrize(
        "authentication",
        ["anonymous", "saved-oidc", "saved-x509", "runtime-token", "runtime-x509"],
    )
    def test_request_authentication_matrix(
        self,
        authentication: str,
        tmp_path: Path,
    ) -> None:
        """Requests apply the selected Authentication source (credential precedence)."""
        cert_path = tmp_path / "client.pem"
        if authentication in {"saved-x509", "runtime-x509"}:
            generate_cert(cert_path)
        client_kwargs: dict[str, object] = {}
        expected_authorization: str | None = None
        expected_type: str | None = None
        expected_url: str | None = None

        if authentication == "saved-oidc":
            credential: OIDCCredential | X509Credential = _oidc(access="saved-access")
            expected_authorization = "Bearer saved-access"
            expected_type = "OIDC"
        elif authentication == "saved-x509":
            credential = X509Credential(idp="test", path=cert_path, expiry=9999999999.0)
            expected_type = "X509"
        else:
            credential = X509Credential(idp="test", path=None)

        config = _configuration(credential)
        if authentication == "runtime-token":
            config = Configuration(
                active=ActiveConfig(authentication="active", server="platform"),
                authentication={
                    "active": X509Credential(idp="active", path=None),
                    "selected": OIDCCredential(
                        idp="selected",
                        client=Client(
                            identity="selected-client",
                            secret=_UNUSABLE_OIDC_SECRETS[0],
                        ),
                        token=Token(refresh=_UNUSABLE_OIDC_SECRETS[1]),
                    ),
                },
                servers={
                    "platform": _server().model_copy(
                        update={"idp": "active"},
                        deep=True,
                    )
                },
            )
            client_kwargs = {
                "authentication_idp": "selected",
                "token": SecretStr("runtime-access"),
                "url": "https://runtime.example/api",
            }
            expected_authorization = "Bearer runtime-access"
            expected_type = "RUNTIME-TOKEN"
            expected_url = "https://runtime.example/api/probe"
        elif authentication == "runtime-x509":
            client_kwargs = {
                "certificate": cert_path,
                "url": "https://runtime.example",
            }
            expected_type = "RUNTIME-X509"
        before_config = config.model_dump(mode="json")

        requests: list[httpx.Request] = []
        transport = httpx.MockTransport(
            lambda request: (
                requests.append(request) or httpx.Response(200, request=request)
            )
        )

        with ExitStack() as stack:
            _enter_clients(stack, transport)
            client = stack.enter_context(HTTPClient(config=config, **client_kwargs))
            response = client.client.get("probe")

        assert response.status_code == 200
        assert len(requests) == 1
        request = requests[0]
        assert request.headers.get("Authorization") == expected_authorization
        assert request.headers.get("X-Skaha-Authentication-Type") == expected_type
        if expected_url is not None:
            assert str(request.url) == expected_url
        assert config.model_dump(mode="json") == before_config
        if authentication == "runtime-token":
            request_material = "\n".join((str(request.url), *request.headers.values()))
            assert all(
                secret not in request_material for secret in _UNUSABLE_OIDC_SECRETS
            )

    async def test_concurrent_requests_share_one_oidc_refresh(
        self,
        tmp_path: Path,
    ) -> None:
        """Concurrent async requests perform one refresh and use its token."""
        now = 1_000.0
        config = _configuration(
            _oidc(access="expired", access_expiry=now - 1, refresh_expiry=now + 1_000)
        )
        token_requests: list[httpx.Request] = []
        platform_requests: list[httpx.Request] = []

        async def refresh_token(request: httpx.Request) -> httpx.Response:
            token_requests.append(request)
            await asyncio.sleep(0.01)
            return httpx.Response(
                200,
                json={
                    "access_token": _REFRESHED_TOKEN,
                    "refresh_token": "rotated-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 300,
                },
                request=request,
            )

        token_transport = httpx.MockTransport(refresh_token)
        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )
        oauth_client = AsyncOAuth2Client(
            "client",
            "secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=token_transport,
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=now),
            patch(
                "canfar.client.AsyncClient",
                side_effect=lambda **kwargs: httpx.AsyncClient(
                    transport=platform_transport, **kwargs
                ),
            ),
            patch(
                "authlib.integrations.httpx_client.AsyncOAuth2Client",
                return_value=oauth_client,
            ),
        ):
            async with HTTPClient(config=config) as client:
                responses = await asyncio.gather(
                    client.asynclient.get("one"),
                    client.asynclient.get("two"),
                )
                persisted = Configuration().authentication["test"]

        assert [response.status_code for response in responses] == [200, 200]
        assert len(token_requests) == 1
        assert [request.headers["Authorization"] for request in platform_requests] == [
            f"Bearer {_REFRESHED_TOKEN}",
            f"Bearer {_REFRESHED_TOKEN}",
        ]
        canonical = config.authentication["test"]
        assert isinstance(canonical, OIDCCredential)
        assert canonical == persisted
        assert canonical.token == Token(
            access=_REFRESHED_TOKEN,
            refresh="rotated-refresh",
            token_type="Bearer",
            scope="openid profile",
        )
        assert canonical.expiry == Expiry(access=1_300.0, refresh=None)

    async def test_refresh_hooks_share_one_client_lock(
        self,
        tmp_path: Path,
    ) -> None:
        """Independent async hook factories cannot race token persistence."""
        now = 1_000.0
        config = _configuration(
            _oidc(access="expired", access_expiry=now - 1, refresh_expiry=now + 1_000)
        )
        token_requests: list[httpx.Request] = []

        async def refresh_token(request: httpx.Request) -> httpx.Response:
            token_requests.append(request)
            await asyncio.sleep(0.01)
            return httpx.Response(
                200,
                json={
                    "access_token": _REFRESHED_TOKEN,
                    "refresh_token": "rotated-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 300,
                },
                request=request,
            )

        token_transport = httpx.MockTransport(refresh_token)
        platform_transport = httpx.MockTransport(
            lambda request: httpx.Response(200, request=request)
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=now),
            patch(
                "canfar.client.AsyncClient",
                side_effect=lambda **kwargs: httpx.AsyncClient(
                    transport=platform_transport, **kwargs
                ),
            ),
            patch(
                "authlib.integrations.httpx_client.AsyncOAuth2Client",
                side_effect=lambda *args, **kwargs: AsyncOAuth2Client(
                    *args, transport=token_transport, **kwargs
                ),
            ),
        ):
            async with HTTPClient(config=config) as client:
                first = arefresh(client)
                second = arefresh(client)
                await asyncio.gather(
                    first(httpx.Request("GET", "https://platform.example/one")),
                    second(httpx.Request("GET", "https://platform.example/two")),
                )

        assert len(token_requests) == 1
        credential = config.authentication["test"]
        assert isinstance(credential, OIDCCredential)
        assert credential.token.access == SecretStr(_REFRESHED_TOKEN)

    async def test_async_refresh_repairs_existing_sync_client(
        self,
        tmp_path: Path,
    ) -> None:
        """A sync request reads a token refreshed by the async client."""
        now = 1_000.0
        config = _configuration(
            _oidc(access="expired", access_expiry=now - 1, refresh_expiry=now + 1_000)
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
                json={
                    "access_token": _REFRESHED_TOKEN,
                    "refresh_token": "rotated-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 300,
                },
                request=request,
            )
        )
        oauth_client = AsyncOAuth2Client(
            "client",
            "secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=token_transport,
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: httpx.Client(
                    transport=platform_transport, **kwargs
                ),
            ),
            patch(
                "canfar.client.AsyncClient",
                side_effect=lambda **kwargs: httpx.AsyncClient(
                    transport=platform_transport, **kwargs
                ),
            ),
            patch(
                "authlib.integrations.httpx_client.AsyncOAuth2Client",
                return_value=oauth_client,
            ),
            HTTPClient(config=config) as client,
        ):
            async with client:
                sync = client.client
                assert sync.headers["Authorization"] == "Bearer expired"
                async_response = await client.asynclient.get("refresh")
                assert sync.headers["Authorization"] == "Bearer expired"
                sync_response = sync.get("after-refresh")
                assert sync.headers["Authorization"] == f"Bearer {_REFRESHED_TOKEN}"
                persisted = Configuration().authentication["test"]

        assert [async_response.status_code, sync_response.status_code] == [200, 200]
        assert [request.headers["Authorization"] for request in platform_requests] == [
            f"Bearer {_REFRESHED_TOKEN}",
            f"Bearer {_REFRESHED_TOKEN}",
        ]
        canonical = config.authentication["test"]
        assert isinstance(canonical, OIDCCredential)
        assert canonical == persisted

    @pytest.mark.parametrize("failure", ["save", "oauth", "network", "malformed"])
    def test_refresh_failure_preserves_last_valid_record(
        self,
        failure: str,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Refresh and persistence failures leave record and request state intact."""
        now = 1_000.0
        sentinel = "secret-refresh-diagnostic"
        config = _configuration(
            _oidc(
                access="old-access",
                refresh="old-refresh",
                access_expiry=now - 1,
                refresh_expiry=now + 1_000,
            ).model_copy(
                update={"client": Client(identity="client", secret="client-secret")}
            )
        )
        original = config.authentication["test"].model_copy(deep=True)
        platform_requests: list[httpx.Request] = []
        token_requests: list[httpx.Request] = []

        def token_endpoint(request: httpx.Request) -> httpx.Response:
            token_requests.append(request)
            if failure == "oauth":
                return httpx.Response(
                    400,
                    json={"error": "invalid_grant", "error_description": sentinel},
                    request=request,
                )
            if failure == "network":
                raise httpx.ConnectError(sentinel, request=request)
            if failure == "malformed":
                return httpx.Response(
                    200,
                    content=sentinel,
                    headers={"Content-Type": "application/json"},
                    request=request,
                )
            return httpx.Response(
                200,
                json={
                    "access_token": _REFRESHED_TOKEN,
                    "refresh_token": "rotated-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 300,
                },
                request=request,
            )

        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )
        oauth_client = OAuth2Client(
            "client",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(token_endpoint),
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch("canfar.models.auth.time.time", return_value=now),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: httpx.Client(
                    transport=platform_transport, **kwargs
                ),
            ),
            patch(
                "authlib.integrations.httpx_client.OAuth2Client",
                return_value=oauth_client,
            ),
            patch(
                "canfar.config.editor.ConfigurationEditor.save",
                side_effect=(OSError(sentinel) if failure == "save" else None),
            ) as save,
            HTTPClient(config=config) as client,
        ):
            request_client = client.client
            expected_error = (
                AuthRequiredError if failure == "oauth" else AuthenticationError
            )
            with pytest.raises(expected_error) as exc_info:
                request_client.get("probe")
            assert request_client.headers["Authorization"] == "Bearer old-access"

        expected_message = (
            "Not authenticated with 'test'.\n"
            "Reason: OIDC refresh credentials were rejected."
            if failure == "oauth"
            else "Failed to refresh OIDC token"
        )
        assert str(exc_info.value) == expected_message
        assert exc_info.value.__cause__ is None
        assert sentinel not in str(exc_info.value)
        assert sentinel not in caplog.text
        assert config.authentication["test"] == original
        assert len(token_requests) == 1
        assert platform_requests == []
        assert save.call_count == int(failure == "save")

    @pytest.mark.parametrize(
        ("state", "persisted_access_expiry", "refresh_expiry", "refreshes", "succeeds"),
        [
            ("valid", 1_100.0, 2_000.0, 0, True),
            ("expired", 900.0, 900.0, 0, False),
            ("refresh-eligible", 900.0, 2_000.0, 1, True),
            ("unrefreshable", 900.0, 2_000.0, 0, False),
        ],
    )
    def test_refresh_and_expiry_outcome_matrix(
        self,
        state: str,
        persisted_access_expiry: float,
        refresh_expiry: float,
        refreshes: int,
        succeeds: bool,
        tmp_path: Path,
    ) -> None:
        """Persisted expiry, not misleading JWT claims, controls refresh."""
        now = 1_000.0
        config = _configuration(
            _oidc(
                access=_MISLEADING_FUTURE_JWT_ACCESS_TOKEN,
                access_expiry=persisted_access_expiry,
                refresh_expiry=refresh_expiry,
            )
        )
        token_requests: list[httpx.Request] = []
        platform_requests: list[httpx.Request] = []
        token_transport = httpx.MockTransport(
            lambda request: (
                token_requests.append(request)
                or httpx.Response(
                    200,
                    json={
                        "access_token": _REFRESHED_TOKEN,
                        "refresh_token": "rotated-refresh",
                        "token_type": "Bearer",
                        "scope": "openid profile",
                        "expires_in": 300,
                    },
                    request=request,
                )
            )
        )
        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )

        with ExitStack() as stack:
            stack.enter_context(
                patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml")
            )
            stack.enter_context(patch("canfar.models.auth.time.time", return_value=now))
            stack.enter_context(
                patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=now)
            )
            _enter_clients(stack, platform_transport, token=token_transport)
            client = stack.enter_context(HTTPClient(config=config))
            request_client = client.client
            if state == "unrefreshable":
                credential = config.authentication["test"]
                assert isinstance(credential, OIDCCredential)
                config.editor.set(
                    "authentication.test",
                    credential.model_copy(
                        update={
                            "endpoints": credential.endpoints.model_copy(
                                update={"discovery": None}
                            )
                        }
                    ),
                )
            if succeeds:
                response = request_client.get("probe")
                assert response.status_code == 200
            else:
                with pytest.raises(AuthRequiredError):
                    request_client.get("probe")

        assert len(token_requests) == refreshes
        assert len(platform_requests) == int(succeeds)
        if state == "refresh-eligible":
            assert platform_requests[0].headers["Authorization"] == (
                f"Bearer {_REFRESHED_TOKEN}"
            )


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    (
        "access",
        "refresh",
        "access_expiry",
        "refresh_expiry",
        "secret_expiry",
        "refreshes",
        "succeeds",
    ),
    [
        pytest.param(
            "saved", None, 1100, None, 900, 0, True, id="access-without-refresh"
        ),
        pytest.param(
            "saved",
            "refresh",
            1100,
            900,
            900,
            0,
            True,
            id="access-outlives-refresh-credentials",
        ),
        pytest.param(None, "refresh", 1100, None, None, 1, True, id="missing-access"),
        pytest.param(
            "saved", "refresh", 900, None, None, 1, True, id="legacy-unknown-expiry"
        ),
        pytest.param(
            "saved", "refresh", 900, None, 0, 1, True, id="nonexpiring-secret"
        ),
        pytest.param(
            "saved", "refresh", 900, 2000, 1000, 0, False, id="expired-secret"
        ),
        pytest.param(
            "saved", "refresh", 900, 1000, 2000, 0, False, id="expired-refresh-token"
        ),
        pytest.param("saved", None, 900, None, 0, 0, False, id="missing-refresh-token"),
    ],
)
async def test_oidc_request_recovery(
    *,
    monkeypatch,
    tmp_path,
    asynchronous,
    access,
    refresh,
    access_expiry,
    refresh_expiry,
    secret_expiry,
    refreshes,
    succeeds,
) -> None:
    """Native requests distinguish access usability from refresh eligibility."""
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml")
    monkeypatch.setattr("canfar.models.auth.time.time", lambda: 1000.0)
    credential = _oidc(
        access=access,
        refresh=refresh,
        access_expiry=access_expiry,
        refresh_expiry=refresh_expiry,
        secret_expiry=secret_expiry,
    )
    config = _configuration(credential)
    token_requests: list[httpx.Request] = []
    platform_requests: list[httpx.Request] = []
    token_transport = httpx.MockTransport(
        lambda request: (
            token_requests.append(request)
            or httpx.Response(
                200,
                json={
                    "access_token": _REFRESHED_TOKEN,
                    "expires_in": 300,
                },
            )
        )
    )
    platform_transport = httpx.MockTransport(
        lambda request: platform_requests.append(request) or httpx.Response(200)
    )
    with ExitStack() as stack:
        _enter_clients(stack, platform_transport, token=token_transport)
        client = stack.enter_context(HTTPClient(config=config))
        async with client:
            with nullcontext() if succeeds else pytest.raises(AuthRequiredError):
                response = (
                    await client.asynclient.get("probe")
                    if asynchronous
                    else client.client.get("probe")
                )
                assert response.status_code == 200

    assert len(token_requests) == refreshes
    assert len(platform_requests) == int(succeeds)
    if succeeds:
        expected_token = _REFRESHED_TOKEN if refreshes else access
        assert (
            platform_requests[0].headers["Authorization"] == f"Bearer {expected_token}"
        )
    if refreshes:
        saved = Configuration().authentication["test"]
        assert isinstance(saved, OIDCCredential)
        assert saved.client.secret_expires_at == secret_expiry


@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "failure",
    ["invalid_client", "invalid_grant", "timeout", "unavailable", "other_oauth"],
)
async def test_oidc_refresh_rejection_requires_login_only_for_credentials(
    monkeypatch,
    tmp_path,
    asynchronous,
    failure,
    caplog,
) -> None:
    """Server rejections support legacy records without diagnosing outages as expiry."""
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)
    config = _configuration(_oidc(access_expiry=1, secret_expiry=None))
    config.editor.save()
    original = config_path.read_bytes()
    token_requests: list[httpx.Request] = []
    platform_requests: list[httpx.Request] = []
    sentinel = "secret-provider-error-description"

    def token_endpoint(request: httpx.Request) -> httpx.Response:
        token_requests.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout(sentinel, request=request)
        if failure == "unavailable":
            return httpx.Response(503, text=sentinel)
        return httpx.Response(
            400,
            json={
                "error": "temporarily_unavailable"
                if failure == "other_oauth"
                else failure,
                "error_description": sentinel,
            },
        )

    platform = httpx.MockTransport(
        lambda request: platform_requests.append(request) or httpx.Response(200)
    )
    needs_login = failure in {"invalid_client", "invalid_grant"}
    with ExitStack() as stack:
        _enter_clients(stack, platform, token=httpx.MockTransport(token_endpoint))
        client = stack.enter_context(HTTPClient(config=config))
        async with client:
            with pytest.raises(
                AuthRequiredError if needs_login else AuthenticationError
            ) as error:
                await client.asynclient.get(
                    "probe"
                ) if asynchronous else client.client.get("probe")

    assert len(token_requests) == 1
    assert platform_requests == []
    assert config_path.read_bytes() == original
    assert sentinel not in str(error.value)
    assert sentinel not in caplog.text
    if needs_login:
        assert error.value.idp == "test"


@pytest.mark.parametrize(
    ("operation", "arguments"),
    [
        ("create", {"name": "batch", "image": "skaha/worker", "replicas": 2}),
        ("logs", {"ids": ["one", "two"]}),
    ],
)
@pytest.mark.parametrize("rejected", [False, True], ids=["outage", "rejected"])
async def test_bulk_requests_preserve_oidc_recovery_errors(
    monkeypatch, tmp_path, operation, arguments, rejected
) -> None:
    """A gathered refresh error remains a client failure with actionable recovery."""
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml")
    config = _configuration(_oidc(access_expiry=1))
    platform_requests: list[httpx.Request] = []
    platform = httpx.MockTransport(
        lambda request: platform_requests.append(request) or httpx.Response(200)
    )
    token = httpx.MockTransport(
        lambda request: httpx.Response(
            400 if rejected else 503,
            json={"error": "invalid_client"},
            request=request,
        )
    )
    with ExitStack() as stack:
        _enter_clients(stack, platform, token=token)
        async with AsyncSession(config=config) as session:
            with pytest.raises(AuthRequiredError if rejected else AuthenticationError):
                await getattr(session, operation)(**arguments)

    assert platform_requests == []
