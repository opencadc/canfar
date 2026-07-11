"""Public contracts for Science Platform Server enrichment."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx
import pytest
from authlib.integrations.httpx_client import OAuth2Client
from pydantic import AnyHttpUrl, AnyUrl

import canfar.server as platform
from canfar.client import HTTPClient
from canfar.exceptions.context import AuthContextError
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
from canfar.models.registry import ContainerRegistry
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    _validate_server,
    discover,
)
from tests.test_auth_x509 import generate_cert

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_CADC_URI = "ivo://cadc.nrc.ca/skaha"
_CADC_URL = "https://ws-uv.canfar.net/skaha"
_REFRESHED_TOKEN = "opaque-refreshed-access-token"
_CONTEXT_PAYLOAD = {
    "cores": {"defaultLimit": None},
    "memoryGB": {"defaultLimit": 192},
    "gpus": {"options": [0, 1, 2, 4]},
}


def _http_client_factory(
    transport: httpx.BaseTransport,
) -> Callable[..., httpx.Client]:
    """Return an HTTPX client factory bound to a test transport."""
    client_type = httpx.Client
    return lambda **kwargs: client_type(transport=transport, **kwargs)


def _server(**updates: object) -> Server:
    """Build a complete CADC Science Platform Server."""
    values = {
        "idp": "cadc",
        "name": "canfar",
        "uri": AnyUrl(_CADC_URI),
        "url": AnyHttpUrl(_CADC_URL),
        "version": "v1",
        "auths": ["x509"],
    }
    values.update(updates)
    return Server(**values)


def _anonymous_config(*servers: Server, idp: str = "cadc") -> Configuration:
    """Build a valid Configuration whose X.509 record has no credential path."""
    return Configuration(
        active=ActiveConfig(authentication=idp, server=None),
        authentication={idp: X509Credential(idp=idp)},
        servers={server.name: server for server in servers if server.name is not None},
    )


def _oidc_credential(
    *,
    access_expiry: float = 9_999_999_999.0,
) -> OIDCCredential:
    """Build a complete SRCNet OIDC Authentication Record."""
    return OIDCCredential(
        idp="srcnet",
        endpoints=Endpoint(
            discovery="https://identity.example/.well-known/openid-configuration",
            token="https://identity.example/token",
        ),
        client=Client(identity="client", secret="client-secret"),
        token=Token(access="target-token", refresh="refresh-token"),
        expiry=Expiry(access=access_expiry, refresh=2_000.0),
    )


def _active_with_target(
    credential: OIDCCredential | X509Credential,
    *,
    registry: ContainerRegistry | None = None,
) -> Configuration:
    """Build active CADC state with an unselected target Authentication Record."""
    active = _server(name="Active-CADC")
    return Configuration(
        active=ActiveConfig(authentication="cadc", server="Active-CADC"),
        authentication={
            "cadc": X509Credential(idp="cadc"),
            credential.idp: credential,
        },
        servers={"Active-CADC": active},
        registry=registry or ContainerRegistry(),
    )


def _capabilities(
    base_url: str,
    *,
    auth_modes: tuple[str, ...] = ("token",),
    version: str = "v2",
) -> str:
    """Return one complete VOSI session capability document."""
    security_methods = "".join(
        f'<securityMethod standardID="ivo://ivoa.net/sso#{mode}" />'
        for mode in auth_modes
    )
    major = version.removeprefix("v").split(".", maxsplit=1)[0]
    return (
        "<capabilities>"
        f'<capability standardID="http://www.opencadc.org/std/platform#session-{major}">'
        "<interface>"
        f'<accessURL use="base">{base_url.rstrip("/")}/{version}</accessURL>'
        f"{security_methods}"
        "</interface>"
        "</capability>"
        "</capabilities>"
    )


class TestPlatformEnrichment:
    """Tests for the public Platform enrichment seam."""

    def test_activation_enriches_resources_and_round_trips_server_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Activation owns HTTP enrichment while Server remains persisted data."""
        known = _server(
            name="Stable-Name",
            cores=8,
            ram=64,
            gpus=1,
            status="reachable",
        )
        requests: list[httpx.Request] = []

        def response(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path.endswith("/capabilities"):
                return httpx.Response(
                    200,
                    text=_capabilities(_CADC_URL),
                    request=request,
                )
            if request.url.path.endswith("/v2/context"):
                return httpx.Response(200, json=_CONTEXT_PAYLOAD, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        config_path = tmp_path / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx.MockTransport(response)),
            ),
        ):
            config = _anonymous_config(known)
            activated = platform.activate(
                "cadc",
                "Stable-Name",
                config=config,
                timeout=7,
            )
            persisted = Configuration()

        assert activated.server.model_dump(mode="json") == {
            **known.model_dump(mode="json"),
            "version": "v2",
            "auths": ["oidc"],
            "cores": 2,
            "ram": 192,
            "gpus": 4,
        }
        assert persisted.active.server == "Stable-Name"
        assert persisted.servers["Stable-Name"] == activated.server
        assert [request.url.path for request in requests] == [
            "/skaha/capabilities",
            "/skaha/v2/context",
        ]
        assert [request.extensions["timeout"] for request in requests] == [
            {"connect": 7, "read": 7, "write": 7, "pool": 7},
            {"connect": 7, "read": 7, "write": 7, "pool": 7},
        ]

    @pytest.mark.parametrize("failure", ["transport", "parse", "validation"])
    def test_activation_uses_resource_defaults_when_context_is_unusable(
        self,
        tmp_path: Path,
        failure: str,
    ) -> None:
        """Expected context failures keep server identity and safe defaults."""
        known = _server(
            name="Stable-Name",
            cores=8,
            ram=64,
            gpus=1,
            status="reachable",
        )

        def response(request: httpx.Request) -> httpx.Response:
            if request.url.path.endswith("/capabilities"):
                return httpx.Response(
                    200,
                    text=_capabilities(_CADC_URL),
                    request=request,
                )
            if failure == "transport":
                message = "context unavailable"
                raise httpx.ConnectError(message, request=request)
            if failure == "parse":
                return httpx.Response(200, content=b"{", request=request)
            return httpx.Response(
                200,
                json={"cores": {"defaultLimit": 0}},
                request=request,
            )

        config_path = tmp_path / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx.MockTransport(response)),
            ),
        ):
            config = _anonymous_config(known)
            activated = platform.activate(
                "cadc",
                "Stable-Name",
                config=config,
            )

        assert (
            activated.server.name,
            activated.server.status,
            activated.server.cores,
            activated.server.ram,
            activated.server.gpus,
        ) == ("Stable-Name", "reachable", 2, 16, 0)

    @pytest.mark.parametrize("authentication", ["oidc", "x509"])
    @pytest.mark.parametrize("strict", [False, True])
    def test_enrich_handles_invalid_saved_authentication_without_state_change(
        self,
        tmp_path: Path,
        authentication: str,
        strict: bool,
    ) -> None:
        """Typed setup failures are safe, request-free, and non-mutating."""
        server = _server()
        credential: OIDCCredential | X509Credential
        if authentication == "oidc":
            credential = OIDCCredential(
                idp="cadc",
                client=Client(identity="client", secret="client-secret"),
                token=Token(refresh="refresh-secret"),
            )
        else:
            credential = X509Credential(
                idp="cadc",
                path=tmp_path,
                expiry=9_999_999_999.0,
            )
        requests: list[httpx.Request] = []
        transport = httpx.MockTransport(
            lambda request: (
                requests.append(request) or httpx.Response(200, request=request)
            )
        )
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(transport),
            ),
        ):
            config = Configuration(
                active=ActiveConfig(authentication="cadc", server="canfar"),
                authentication={"cadc": credential},
                servers={"canfar": server},
            )
            config.save()
            before_model = config.model_dump(mode="json")
            before_yaml = config_path.read_bytes()
            if strict:
                with pytest.raises(ServerFetchError) as exc_info:
                    platform.enrich(server, config=config, strict=True)
                assert isinstance(exc_info.value.__cause__, AuthContextError)
                message = str(exc_info.value)
                assert "client-secret" not in message
                assert "refresh-secret" not in message
            else:
                assert platform.enrich(server, config=config, strict=False) == server

        assert requests == []
        assert config.model_dump(mode="json") == before_model
        assert config_path.read_bytes() == before_yaml

    def test_http_client_authentication_selector_is_transient(
        self,
        tmp_path: Path,
    ) -> None:
        """The request-only IDP selector is resolved but never serialized."""
        with patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"):
            config = _active_with_target(_oidc_credential())
            before_active = config.active.model_dump(mode="json")
            client = HTTPClient(
                config=config,
                authentication_idp="srcnet",
                url="https://srcnet.example/skaha",
            )

        assert isinstance(client.authentication_record, OIDCCredential)
        assert "authentication_idp" not in client.model_dump(mode="json")
        assert config.active.model_dump(mode="json") == before_active

    def test_enrich_returns_validated_capability_metadata(
        self,
        tmp_path: Path,
    ) -> None:
        """Capabilities replace endpoint facts without dropping known metadata."""
        known = _server(
            name="Known-CADC",
            url=AnyHttpUrl("https://registry.example/skaha"),
            cores=8,
            ram=64,
            gpus=1,
            status="reachable",
        )
        expected = known.model_copy(
            update={
                "url": AnyHttpUrl("https://api.example/skaha"),
                "version": "v2",
                "auths": ["x509", "oidc"],
            },
            deep=True,
        )
        capabilities = _capabilities(
            "https://api.example/skaha",
            auth_modes=("token", "tls-with-certificate"),
        )

        def response(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == "https://registry.example/skaha/capabilities"
            return httpx.Response(200, text=capabilities, request=request)

        transport = httpx.MockTransport(response)
        config_path = tmp_path / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(transport),
            ),
        ):
            config = _anonymous_config(known)
            enriched = platform.enrich(known, config=config, timeout=7)

        assert enriched == expected

    def test_enrich_uses_target_authentication_without_selecting_it(
        self,
        tmp_path: Path,
    ) -> None:
        """A non-active saved OIDC record authorizes only the target request."""
        target = _server(
            idp="srcnet",
            name="SRCNet",
            uri=AnyUrl("ivo://srcnet.example/skaha"),
            url=AnyHttpUrl("https://srcnet.example/skaha"),
        )
        capabilities = _capabilities("https://srcnet.example/skaha")
        observed_headers: dict[str, str | None] = {}

        def response(request: httpx.Request) -> httpx.Response:
            observed_headers.update(
                {
                    "authorization": request.headers.get("Authorization"),
                    "auth_type": request.headers.get("X-Skaha-Authentication-Type"),
                    "accept": request.headers.get("Accept"),
                    "content_type": request.headers.get("Content-Type"),
                    "registry": request.headers.get("X-Skaha-Registry-Auth"),
                }
            )
            return httpx.Response(200, text=capabilities, request=request)

        transport = httpx.MockTransport(response)
        config_path = tmp_path / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(transport),
            ),
            patch("canfar.client.log") as client_log,
            patch("canfar.hooks.httpx.auth.log") as auth_log,
            patch("canfar.hooks.httpx.expiry.log") as expiry_log,
            patch("canfar.server.log") as platform_log,
        ):
            config = _active_with_target(
                _oidc_credential(),
                registry=ContainerRegistry(
                    username="registry-user",
                    secret="registry-secret",
                ),
            )
            before = config.model_dump(mode="json")
            encoded_registry_secret = config.registry.encoded()
            enriched = platform.enrich(target, config=config)
            log_calls = (
                f"{client_log.mock_calls}{auth_log.mock_calls}"
                f"{expiry_log.mock_calls}{platform_log.mock_calls}"
            )

        assert (
            enriched.auths,
            config.model_dump(mode="json"),
            config_path.exists(),
            observed_headers,
        ) == (
            ["oidc"],
            before,
            False,
            {
                "authorization": "Bearer target-token",
                "auth_type": "OIDC",
                "accept": "application/xml",
                "content_type": None,
                "registry": None,
            },
        )
        assert "registry-secret" not in log_calls
        assert encoded_registry_secret not in log_calls

    def test_enrich_uses_target_x509_without_changing_selection(
        self,
        tmp_path: Path,
    ) -> None:
        """A non-active saved X.509 record keeps its canonical auth header."""
        certificate = tmp_path / "target.pem"
        generate_cert(certificate)
        target = _server(
            idp="srcnet",
            name="SRCNet",
            uri=AnyUrl("ivo://srcnet.example/skaha"),
            url=AnyHttpUrl("https://srcnet.example/skaha"),
        )
        capabilities = _capabilities(
            "https://srcnet.example/skaha",
            auth_modes=("tls-with-certificate",),
        )
        observed_auth_type: str | None = None

        def response(request: httpx.Request) -> httpx.Response:
            nonlocal observed_auth_type
            observed_auth_type = request.headers.get("X-Skaha-Authentication-Type")
            return httpx.Response(200, text=capabilities, request=request)

        with patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"):
            config = _active_with_target(
                X509Credential(
                    idp="srcnet",
                    path=certificate,
                    expiry=9_999_999_999.0,
                )
            )
            before = config.model_dump(mode="json")
            with patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx.MockTransport(response)),
            ):
                enriched = platform.enrich(target, config=config)

        assert (enriched.auths, observed_auth_type, config.model_dump(mode="json")) == (
            ["x509"],
            "X509",
            before,
        )

    def test_enrich_missing_target_authentication_is_anonymous(
        self,
        tmp_path: Path,
    ) -> None:
        """An unknown target IDP can use public capabilities without mutation."""
        target = _server(
            idp="missing",
            name="Missing",
            uri=AnyUrl("ivo://missing.example/skaha"),
            url=AnyHttpUrl("https://missing.example/skaha"),
        )
        capabilities = _capabilities("https://missing.example/skaha")
        observed_headers: dict[str, str | None] = {}

        def response(request: httpx.Request) -> httpx.Response:
            observed_headers.update(
                {
                    "authorization": request.headers.get("Authorization"),
                    "auth_type": request.headers.get("X-Skaha-Authentication-Type"),
                }
            )
            return httpx.Response(200, text=capabilities, request=request)

        with patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"):
            active = _server(name="Active-CADC")
            config = Configuration(
                active=ActiveConfig(authentication="cadc", server="Active-CADC"),
                authentication={"cadc": X509Credential(idp="cadc")},
                servers={"Active-CADC": active},
            )
            before = config.model_dump(mode="json")
            with patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx.MockTransport(response)),
            ):
                enriched = platform.enrich(target, config=config)

        assert (
            enriched.version,
            observed_headers,
            config.model_dump(mode="json"),
        ) == (
            "v2",
            {"authorization": None, "auth_type": None},
            before,
        )

    def test_refresh_can_persist_without_candidate_platform_state(
        self,
        tmp_path: Path,
    ) -> None:
        """Target refresh survives a context failure without selecting its Server."""
        now = 1_000.0
        refreshed_token = _REFRESHED_TOKEN
        target = _server(
            idp="srcnet",
            name="SRCNet",
            uri=AnyUrl("ivo://srcnet.example/skaha"),
            url=AnyHttpUrl("https://srcnet.example/skaha"),
            version=None,
            auths=None,
        )
        capabilities = _capabilities("https://srcnet.example/skaha")
        platform_requests: list[httpx.Request] = []
        token_requests: list[httpx.Request] = []

        def platform_response(request: httpx.Request) -> httpx.Response:
            platform_requests.append(request)
            if request.url.path.endswith("/capabilities"):
                return httpx.Response(200, text=capabilities, request=request)
            if request.url.path.endswith("/v2/context"):
                return httpx.Response(503, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        def token_response(request: httpx.Request) -> httpx.Response:
            token_requests.append(request)
            return httpx.Response(
                200,
                json={
                    "access_token": refreshed_token,
                    "refresh_token": "rotated-refresh",
                    "token_type": "Bearer",
                    "scope": "openid profile",
                    "expires_in": 300,
                },
                request=request,
            )

        client_type = httpx.Client
        oauth_client = OAuth2Client(
            "client-id",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(token_response),
        )
        config_path = tmp_path / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.models.auth.time.time", return_value=now),
            patch("authlib.oauth2.rfc6749.wrappers.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: client_type(
                    transport=httpx.MockTransport(platform_response),
                    **kwargs,
                ),
            ),
            patch(
                "authlib.integrations.httpx_client.OAuth2Client",
                return_value=oauth_client,
            ),
        ):
            config = _active_with_target(_oidc_credential(access_expiry=now - 1))
            config.save()
            before_active = config.active.model_dump(mode="json")
            before_servers = {
                name: server.model_dump(mode="json")
                for name, server in config.servers.items()
            }

            validated = _validate_server(
                target,
                config=config,
                idp="srcnet",
                timeout=7,
            )
            persisted = Configuration()

        refreshed = config.get_credential("srcnet")
        saved_refreshed = persisted.get_credential("srcnet")
        assert isinstance(refreshed, OIDCCredential)
        assert isinstance(saved_refreshed, OIDCCredential)
        assert (
            validated.version,
            len(token_requests),
            [request.headers["Authorization"] for request in platform_requests],
            [request.extensions["timeout"] for request in platform_requests],
            config.active.model_dump(mode="json"),
            {
                name: server.model_dump(mode="json")
                for name, server in config.servers.items()
            },
            persisted.active.model_dump(mode="json"),
            {
                name: server.model_dump(mode="json")
                for name, server in persisted.servers.items()
            },
            refreshed.token.access.get_secret_value()
            if refreshed.token.access is not None
            else None,
            saved_refreshed.token.access.get_secret_value()
            if saved_refreshed.token.access is not None
            else None,
        ) == (
            "v2",
            1,
            [f"Bearer {refreshed_token}", f"Bearer {refreshed_token}"],
            [
                {"connect": 7, "read": 7, "write": 7, "pool": 7},
                {"connect": 7, "read": 7, "write": 7, "pool": 7},
            ],
            before_active,
            before_servers,
            before_active,
            before_servers,
            refreshed_token,
            refreshed_token,
        )

    def test_refresh_failure_leaves_all_platform_state_unchanged(
        self,
        tmp_path: Path,
    ) -> None:
        """A failed target refresh cannot mutate memory or persisted state."""
        now = 1_000.0
        target = _server(
            idp="srcnet",
            name="SRCNet",
            uri=AnyUrl("ivo://srcnet.example/skaha"),
            url=AnyHttpUrl("https://srcnet.example/skaha"),
            version=None,
            auths=None,
        )
        platform_requests: list[httpx.Request] = []
        client_type = httpx.Client
        config_path = tmp_path / "config.yaml"
        platform_transport = httpx.MockTransport(
            lambda request: (
                platform_requests.append(request)
                or httpx.Response(200, request=request)
            )
        )
        token_transport = httpx.MockTransport(
            lambda request: httpx.Response(503, request=request)
        )
        oauth_client = OAuth2Client(
            "client-id",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=token_transport,
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.models.auth.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: client_type(
                    transport=platform_transport,
                    **kwargs,
                ),
            ),
            patch(
                "authlib.integrations.httpx_client.OAuth2Client",
                return_value=oauth_client,
            ),
        ):
            config = _active_with_target(_oidc_credential(access_expiry=now - 1))
            config.save()
            before_model = config.model_dump(mode="json")
            before_yaml = config_path.read_bytes()

            with pytest.raises(ServerFetchError, match="Failed to fetch capabilities"):
                platform.enrich(target, config=config)

        assert (
            config.model_dump(mode="json"),
            config_path.read_bytes(),
            platform_requests,
        ) == (before_model, before_yaml, [])

    @pytest.mark.parametrize("failure", ["unauthorized", "network"])
    def test_discover_failure_does_not_change_configuration(
        self,
        tmp_path: Path,
        failure: str,
    ) -> None:
        """Auth and network failures leave memory and YAML byte-for-byte unchanged."""
        registry_url = "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
        registry_body = f"{_CADC_URI}={_CADC_URL}/capabilities"

        def registry_response(request: httpx.Request) -> httpx.Response:
            if request.method == "GET" and str(request.url) == registry_url:
                return httpx.Response(200, text=registry_body, request=request)
            if request.method == "HEAD" and str(request.url) == _CADC_URL:
                return httpx.Response(200, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        def unavailable(request: httpx.Request) -> httpx.Response:
            if failure == "network":
                message = "connection refused"
                raise httpx.ConnectError(message, request=request)
            return httpx.Response(401, request=request)

        async_transport = httpx.MockTransport(registry_response)
        capabilities_transport = httpx.MockTransport(unavailable)
        async_client_type = httpx.AsyncClient
        config_path = tmp_path / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.utils.discover.httpx.AsyncClient",
                side_effect=lambda **kwargs: async_client_type(
                    transport=async_transport,
                    **kwargs,
                ),
            ),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(capabilities_transport),
            ),
        ):
            config = _anonymous_config()
            config.save()
            before_model = config.model_dump(mode="json")
            before_yaml = config_path.read_bytes()
            with pytest.raises(ServerDiscoveryError, match="No servers discovered"):
                discover("cadc", config=config)

        assert (config.model_dump(mode="json"), config_path.read_bytes()) == (
            before_model,
            before_yaml,
        )

    @pytest.mark.parametrize("strict", [False, True])
    def test_enrich_handles_malformed_capabilities(
        self,
        tmp_path: Path,
        strict: bool,
    ) -> None:
        """Malformed capability XML is safe or explicit according to strictness."""
        server = _server(version=None, auths=None)
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                text="<capabilities>",
                request=request,
            )
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(transport),
            ),
        ):
            if strict:
                with pytest.raises(
                    ServerFetchError,
                    match="Failed to fetch capabilities",
                ):
                    platform.enrich(
                        server,
                        config=_anonymous_config(),
                        strict=True,
                    )
                return

            enriched = platform.enrich(
                server,
                config=_anonymous_config(),
                strict=False,
            )

        assert enriched == server

    @pytest.mark.parametrize("strict", [False, True])
    def test_enrich_does_not_hide_unexpected_transport_defects(
        self,
        tmp_path: Path,
        strict: bool,
    ) -> None:
        """Programming defects escape in strict and discovery enrichment."""
        server = _server()

        def unexpected(_request: httpx.Request) -> httpx.Response:
            message = "unexpected platform route"
            raise AssertionError(message)

        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx.MockTransport(unexpected)),
            ),
            pytest.raises(AssertionError, match="unexpected platform route"),
        ):
            platform.enrich(
                server,
                config=_anonymous_config(),
                strict=strict,
            )
