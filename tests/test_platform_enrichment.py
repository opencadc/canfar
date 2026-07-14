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


def _patch_client(tmp_path: Path, transport: httpx.BaseTransport):
    """Patch CONFIG_PATH and the sync HTTPX client factory."""
    return (
        patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
        patch("canfar.client.Client", side_effect=_http_client_factory(transport)),
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
            """Serve capabilities and context for activation enrichment."""
            requests.append(request)
            if request.url.path.endswith("/capabilities"):
                return httpx.Response(
                    200, text=_capabilities(_CADC_URL), request=request
                )
            if request.url.path.endswith("/v2/context"):
                return httpx.Response(200, json=_CONTEXT_PAYLOAD, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        config_patch, client_patch = _patch_client(
            tmp_path, httpx.MockTransport(response)
        )
        with config_patch, client_patch:
            config = _anonymous_config(known)
            activated = platform.activate(
                "cadc", "Stable-Name", config=config, timeout=7
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
        known = _server(name="Stable-Name", cores=8, ram=64, gpus=1, status="reachable")

        def response(request: httpx.Request) -> httpx.Response:
            """Serve capabilities and a parametrized unusable context reply."""
            if request.url.path.endswith("/capabilities"):
                return httpx.Response(
                    200, text=_capabilities(_CADC_URL), request=request
                )
            if failure == "transport":
                message = "context unavailable"
                raise httpx.ConnectError(message, request=request)
            if failure == "parse":
                return httpx.Response(200, content=b"{", request=request)
            return httpx.Response(
                200, json={"cores": {"defaultLimit": 0}}, request=request
            )

        config_patch, client_patch = _patch_client(
            tmp_path, httpx.MockTransport(response)
        )
        with config_patch, client_patch:
            activated = platform.activate(
                "cadc", "Stable-Name", config=_anonymous_config(known)
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
        if authentication == "oidc":
            credential: OIDCCredential | X509Credential = OIDCCredential(
                idp="cadc",
                client=Client(identity="client", secret="client-secret"),
                token=Token(refresh="refresh-secret"),
            )
        else:
            credential = X509Credential(
                idp="cadc", path=tmp_path, expiry=9_999_999_999.0
            )
        requests: list[httpx.Request] = []
        transport = httpx.MockTransport(
            lambda request: (
                requests.append(request) or httpx.Response(200, request=request)
            )
        )
        config_path = tmp_path / "config.yaml"

        config_patch, client_patch = _patch_client(tmp_path, transport)
        with config_patch, client_patch:
            config = Configuration(
                active=ActiveConfig(authentication="cadc", server="canfar"),
                authentication={"cadc": credential},
                servers={"canfar": server},
            )
            config.save()
            before_model = config.model_dump(mode="json")
            before_yaml = config_path.read_bytes()
            if strict:
                with pytest.raises(platform.ServerFetchError) as exc_info:
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
            """Serve validated capability metadata for enrich."""
            assert str(request.url) == "https://registry.example/skaha/capabilities"
            return httpx.Response(200, text=capabilities, request=request)

        config_patch, client_patch = _patch_client(
            tmp_path, httpx.MockTransport(response)
        )
        with config_patch, client_patch:
            enriched = platform.enrich(
                known, config=_anonymous_config(known), timeout=7
            )

        assert enriched == expected

    @pytest.mark.parametrize(
        "source",
        ["target-oidc", "target-x509", "missing"],
    )
    def test_enrich_uses_target_authentication_without_selecting_it(
        self,
        tmp_path: Path,
        source: str,
    ) -> None:
        """Target auth authorizes enrich without mutating active selection."""
        if source == "missing":
            target = _server(
                idp="missing",
                name="Missing",
                uri=AnyUrl("ivo://missing.example/skaha"),
                url=AnyHttpUrl("https://missing.example/skaha"),
            )
            auth_modes: tuple[str, ...] = ("token",)
            expected_auth = (None, None)
            expected_auths = ["oidc"]
        else:
            target = _server(
                idp="srcnet",
                name="SRCNet",
                uri=AnyUrl("ivo://srcnet.example/skaha"),
                url=AnyHttpUrl("https://srcnet.example/skaha"),
            )
            if source == "target-x509":
                auth_modes = ("tls-with-certificate",)
                expected_auth = (None, "X509")
                expected_auths = ["x509"]
            else:
                auth_modes = ("token",)
                expected_auth = ("Bearer target-token", "OIDC")
                expected_auths = ["oidc"]

        capabilities = _capabilities(str(target.url).rstrip("/"), auth_modes=auth_modes)
        observed: dict[str, str | None] = {}
        config_path = tmp_path / "config.yaml"

        def response(request: httpx.Request) -> httpx.Response:
            """Capture enrich capabilities request headers and return XML."""
            observed["authorization"] = request.headers.get("Authorization")
            observed["auth_type"] = request.headers.get("X-Skaha-Authentication-Type")
            observed["accept"] = request.headers.get("Accept")
            observed["content_type"] = request.headers.get("Content-Type")
            observed["registry"] = request.headers.get("X-Skaha-Registry-Auth")
            return httpx.Response(200, text=capabilities, request=request)

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            if source == "missing":
                config = Configuration(
                    active=ActiveConfig(authentication="cadc", server="Active-CADC"),
                    authentication={"cadc": X509Credential(idp="cadc")},
                    servers={"Active-CADC": _server(name="Active-CADC")},
                )
            elif source == "target-x509":
                certificate = tmp_path / "target.pem"
                generate_cert(certificate)
                config = _active_with_target(
                    X509Credential(
                        idp="srcnet", path=certificate, expiry=9_999_999_999.0
                    )
                )
            else:
                config = _active_with_target(
                    _oidc_credential(),
                    registry=ContainerRegistry(
                        username="registry-user", secret="registry-secret"
                    ),
                )
            before = config.model_dump(mode="json")
            with patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx.MockTransport(response)),
            ):
                enriched = platform.enrich(target, config=config)

        assert enriched.auths == expected_auths
        assert (observed["authorization"], observed["auth_type"]) == expected_auth
        assert observed["accept"] == "application/xml"
        assert observed["content_type"] is None
        assert observed["registry"] is None
        assert config.model_dump(mode="json") == before
        assert config_path.exists() is False

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

    def test_refresh_can_persist_without_candidate_platform_state(
        self,
        tmp_path: Path,
    ) -> None:
        """Target refresh survives a context failure without selecting its Server."""
        now = 1_000.0
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
            """Serve capabilities then a failed context fetch during refresh."""
            platform_requests.append(request)
            if request.url.path.endswith("/capabilities"):
                return httpx.Response(200, text=capabilities, request=request)
            if request.url.path.endswith("/v2/context"):
                return httpx.Response(503, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        def token_response(request: httpx.Request) -> httpx.Response:
            """Return a successful OIDC token refresh payload."""
            token_requests.append(request)
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
                side_effect=lambda **kwargs: httpx.Client(
                    transport=httpx.MockTransport(platform_response), **kwargs
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
            validated = platform._validate_server(  # noqa: SLF001
                target, config=config, idp="srcnet", timeout=7
            )
            persisted = Configuration()

        refreshed = config.get_credential("srcnet")
        saved_refreshed = persisted.get_credential("srcnet")
        assert isinstance(refreshed, OIDCCredential)
        assert isinstance(saved_refreshed, OIDCCredential)
        assert validated.version == "v2"
        assert len(token_requests) == 1
        assert [request.headers["Authorization"] for request in platform_requests] == [
            f"Bearer {_REFRESHED_TOKEN}",
            f"Bearer {_REFRESHED_TOKEN}",
        ]
        assert config.active.model_dump(mode="json") == before_active
        assert {
            name: server.model_dump(mode="json")
            for name, server in config.servers.items()
        } == before_servers
        assert persisted.active.model_dump(mode="json") == before_active
        assert refreshed.token.access is not None
        assert refreshed.token.access.get_secret_value() == _REFRESHED_TOKEN
        assert saved_refreshed.token.access is not None
        assert saved_refreshed.token.access.get_secret_value() == _REFRESHED_TOKEN

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
        config_path = tmp_path / "config.yaml"
        oauth_client = OAuth2Client(
            "client-id",
            "client-secret",
            token_endpoint_auth_method="client_secret_basic",
            transport=httpx.MockTransport(
                lambda request: httpx.Response(503, request=request)
            ),
        )

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.models.auth.time.time", return_value=now),
            patch(
                "canfar.client.Client",
                side_effect=lambda **kwargs: httpx.Client(
                    transport=httpx.MockTransport(
                        lambda request: (
                            platform_requests.append(request)
                            or httpx.Response(200, request=request)
                        )
                    ),
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
            with pytest.raises(
                platform.ServerFetchError, match="Failed to fetch capabilities"
            ):
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
            """Serve CADC registry contents for discovery before enrich fails."""
            if request.method == "GET" and str(request.url) == registry_url:
                return httpx.Response(200, text=registry_body, request=request)
            if request.method == "HEAD" and str(request.url) == _CADC_URL:
                return httpx.Response(200, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        def unavailable(request: httpx.Request) -> httpx.Response:
            """Simulate auth or transport failure during capability fetch."""
            if failure == "network":
                message = "connection refused"
                raise httpx.ConnectError(message, request=request)
            return httpx.Response(401, request=request)

        class _RegistryAsyncClient(httpx.AsyncClient):
            def __init__(self, **kwargs: object) -> None:
                kwargs["transport"] = httpx.MockTransport(registry_response)
                super().__init__(**kwargs)

        config_path = tmp_path / "config.yaml"
        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.utils.discover.httpx.AsyncClient", _RegistryAsyncClient),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx.MockTransport(unavailable)),
            ),
        ):
            config = _anonymous_config()
            config.save()
            before_model = config.model_dump(mode="json")
            before_yaml = config_path.read_bytes()
            with pytest.raises(
                platform.ServerDiscoveryError, match="No servers discovered"
            ):
                platform.discover("cadc", config=config)

        assert (config.model_dump(mode="json"), config_path.read_bytes()) == (
            before_model,
            before_yaml,
        )

    @pytest.mark.parametrize(
        ("mode", "strict", "raises"),
        [
            ("malformed", False, None),
            ("malformed", True, platform.ServerFetchError),
            ("unexpected", False, AssertionError),
            ("unexpected", True, AssertionError),
        ],
        ids=["malformed-keep", "malformed-strict", "unexpected", "unexpected-strict"],
    )
    def test_enrich_fail_or_keep_outcomes(
        self,
        tmp_path: Path,
        mode: str,
        strict: bool,
        raises: type[BaseException] | None,
    ) -> None:
        """Strictness keeps known servers on parse failure; defects still escape."""
        server = _server(version=None, auths=None) if mode == "malformed" else _server()

        def handler(request: httpx.Request) -> httpx.Response:
            """Return malformed capabilities or raise an unexpected defect."""
            if mode == "unexpected":
                message = "unexpected platform route"
                raise AssertionError(message)
            return httpx.Response(200, text="<capabilities>", request=request)

        config_patch, client_patch = _patch_client(
            tmp_path, httpx.MockTransport(handler)
        )
        with config_patch, client_patch:
            if raises is None:
                assert (
                    platform.enrich(server, config=_anonymous_config(), strict=strict)
                    == server
                )
                return
            match = (
                "Failed to fetch capabilities"
                if raises is platform.ServerFetchError
                else "unexpected platform route"
            )
            with pytest.raises(raises, match=match):
                platform.enrich(server, config=_anonymous_config(), strict=strict)
