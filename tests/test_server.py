"""Behavior tests for the server selection and discovery seam."""

from __future__ import annotations

from pathlib import Path
from threading import Barrier
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl

from canfar.errors import ErrorCode
from canfar.models.active import ActiveConfig
from canfar.models.auth import OIDCCredential, X509Credential
from canfar.models.config import Configuration
from canfar.models.http import Server, VOSpaceService
from canfar.models.registry import IVOARegistry, IVOARegistrySearch
from canfar.models.registry import Server as DiscoveredServer
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    ServerSelectionRequiredError,
    _discover_for_idp,
    _discovered_to_server,
    _select_storage_resource,
    activate,
    discover,
    enrich,
    use,
)
from canfar.server import (
    list_servers as server_list,
)
from canfar.utils.discover import Discover
from tests.helpers.config import assign_servers

if TYPE_CHECKING:
    from collections.abc import Callable

_CADC_URI = "ivo://cadc.nrc.ca/skaha"
_CADC_URL = "https://ws-uv.canfar.net/skaha"

_VOSPACE_CAPABILITIES = """
    <capabilities xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <capability standardID="ivo://ivoa.net/std/VOSpace/v2.0#nodes">
        <interface xsi:type="ParamHTTP" role="std">
          <accessURL use="base">https://storage.example/arc/nodes</accessURL>
        </interface>
      </capability>
    </capabilities>
"""


def _http_client_factory(
    transport: httpx.BaseTransport,
) -> Callable[..., httpx.Client]:
    """Return an HTTPX client factory bound to a test transport."""
    client_type = httpx.Client
    return lambda **kwargs: client_type(transport=transport, **kwargs)


def _cadc_server(**updates: object) -> Server:
    """Build a default CADC server record for tests."""
    base = {
        "idp": "cadc",
        "name": "CADC-CANFAR",
        "uri": AnyUrl(_CADC_URI),
        "url": AnyHttpUrl(_CADC_URL),
        "version": "v1",
        "auths": ["x509"],
    }
    base.update(updates)
    return Server(**base)


def _anonymous_config(*servers: Server, idp: str = "cadc") -> Configuration:
    """Build a valid Configuration whose X.509 record has no credential path."""
    return Configuration(
        active=ActiveConfig(authentication=idp, server=None),
        authentication={idp: X509Credential(idp=idp)},
        servers={server.name: server for server in servers if server.name is not None},
    )


class TestServerList:
    """Tests for canfar.server.list()."""

    def test_list_returns_servers_for_active_idp(self, tmp_path: Path) -> None:
        """Known servers are scoped to the active Identity Provider."""
        cadc = _cadc_server()
        srcnet = _cadc_server(
            idp="srcnet",
            name="SRCNet-Sweden",
            uri=AnyUrl("ivo://swesrc.chalmers.se/skaha"),
            url=AnyHttpUrl("https://services.swesrc.chalmers.se/skaha"),
        )
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, cadc, srcnet)
            config.active = config.active.model_copy(update={"authentication": "cadc"})
            config.save()

            with patch("canfar.server.Configuration", Configuration):
                servers = server_list()

        assert len(servers) == 1
        assert servers[0].idp == "cadc"
        assert servers[0].name == "CADC-CANFAR"

    def test_list_empty_when_no_servers_for_active_idp(self, tmp_path: Path) -> None:
        """An IDP with no saved servers returns an empty list."""
        cadc = _cadc_server()
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.authentication = {
                "cadc": X509Credential(
                    idp="cadc", path=Path.home() / ".ssl" / "cadcproxy.pem"
                ),
                "srcnet": OIDCCredential(idp="srcnet"),
            }
            assign_servers(config, cadc)
            config.active = config.active.model_copy(
                update={"authentication": "srcnet", "server": "CADC-CANFAR"}
            )
            config_path.write_text(
                yaml.dump(config.model_dump(mode="json", exclude_none=True)),
                encoding="utf-8",
            )

            with patch("canfar.server.Configuration", Configuration):
                servers = server_list(discover_if_empty=False)

        assert servers == []


class TestServerUse:
    """Tests for canfar.server.use()."""

    def test_use_by_uri_updates_active_server(self, tmp_path: Path) -> None:
        """Selecting by URI fetches, validates, and saves the active server."""
        target = _cadc_server()
        fetched = target.model_copy(
            update={"cores": 16, "ram": 192, "gpus": 4},
            deep=True,
        )
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, target)
            config.save()

            with (
                patch(
                    "canfar.server._validate_server",
                    return_value=fetched,
                ) as mock_validate,
                patch("canfar.server.Configuration", Configuration),
            ):
                use(_CADC_URI)

            saved = Configuration()
            assert saved.active.server == "CADC-CANFAR"
            mock_validate.assert_called_once()

    def test_use_by_unique_name_updates_active_server(self, tmp_path: Path) -> None:
        """Selecting by unique display name resolves and saves."""
        target = _cadc_server(name="CADC-CANFAR")
        fetched = target.model_copy(update={"cores": 8, "ram": 64}, deep=True)
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, target)
            config.save()

            with (
                patch("canfar.server._validate_server", return_value=fetched),
                patch("canfar.server.Configuration", Configuration),
            ):
                use("CADC-CANFAR")

            saved = Configuration()
            assert saved.active.server == "CADC-CANFAR"

    def test_use_unknown_name_fails_without_changing_active_server(
        self, tmp_path: Path
    ) -> None:
        """Unknown Server Name selectors fail without changing active server."""
        target = _cadc_server()
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, target)
            config.save()
            previous = Configuration().active.server

            with (
                patch("canfar.server._resolve_selector", return_value=None),
                patch(
                    "canfar.server.discover",
                    side_effect=ServerDiscoveryError("registry down"),
                ),
                patch("canfar.server.Configuration", Configuration),
                pytest.raises(ServerDiscoveryError),
            ):
                use("missing-server")

            assert Configuration().active.server == previous

    def test_use_runs_discovery_on_miss_then_succeeds(self, tmp_path: Path) -> None:
        """Unknown selectors trigger one discovery pass before retry."""
        known = _cadc_server()
        discovered = _cadc_server(
            name="SRCNet-UK",
            uri=AnyUrl("ivo://canfar.cam.uksrc.org/skaha"),
            url=AnyHttpUrl("https://canfar.cam.uksrc.org/skaha"),
        )
        fetched = discovered.model_copy(update={"cores": 16, "ram": 192}, deep=True)
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, known)
            config.save()

            def merge_discovered(
                _idp: str,
                *,
                config: Configuration,
                **_kwargs: object,
            ) -> list[Server]:
                config.upsert_server(discovered)
                return [discovered]

            with (
                patch(
                    "canfar.server.discover",
                    side_effect=merge_discovered,
                ),
                patch("canfar.server._validate_server", return_value=fetched),
                patch("canfar.server.Configuration", Configuration),
            ):
                use("ivo://canfar.cam.uksrc.org/skaha")

            saved = Configuration()
            assert saved.active.server == "SRCNet-UK"

    def test_use_discovery_failure_leaves_active_unchanged(
        self,
        tmp_path: Path,
    ) -> None:
        """Discovery failure does not change the active server."""
        target = _cadc_server()
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, target)
            config.save()
            previous = Configuration().active.server

            with (
                patch("canfar.server._resolve_selector", return_value=None),
                patch(
                    "canfar.server.discover",
                    side_effect=ServerDiscoveryError("registry down"),
                ),
                patch("canfar.server.Configuration", Configuration),
                pytest.raises(ServerDiscoveryError),
            ):
                use("missing-server")

            assert Configuration().active.server == previous

    def test_use_fetch_failure_leaves_active_unchanged(self, tmp_path: Path) -> None:
        """Fetch or validation failure leaves the previous active server."""
        target = _cadc_server()
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, target)
            config.save()
            previous = Configuration().active.server

            with (
                patch(
                    "canfar.server._validate_server",
                    side_effect=ServerFetchError("context unavailable"),
                ),
                patch("canfar.server.Configuration", Configuration),
                pytest.raises(ServerFetchError),
            ):
                use(_CADC_URI)

            assert Configuration().active.server == previous


class TestServerDiscovery:
    """Tests for IDP-scoped discovery helpers."""

    def test_discover_returns_canonical_state_for_duplicate_server_names(
        self,
        tmp_path: Path,
    ) -> None:
        """Returned and saved discovery state share one deterministic winner."""
        alpha = _cadc_server(
            name="Alpha",
            uri=AnyUrl("ivo://alpha.example/skaha"),
            url=AnyHttpUrl("https://alpha.example/skaha"),
        )
        earlier = _cadc_server(
            name="Duplicate",
            uri=AnyUrl("ivo://a.example/skaha"),
            url=AnyHttpUrl("https://a.example/skaha"),
        )
        winner = _cadc_server(
            name="Duplicate",
            uri=AnyUrl("ivo://z.example/skaha"),
            url=AnyHttpUrl("https://z.example/skaha"),
        )
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar.server._discover_for_idp",
                return_value=[winner, alpha, earlier],
            ),
        ):
            config = _anonymous_config()
            discovered = discover("cadc", config=config)
            persisted = Configuration()

        assert discovered == [alpha, winner]
        assert list(config.servers.values()) == discovered
        assert list(persisted.servers.values()) == discovered

    def test_discover_merges_servers_through_public_api(self, tmp_path: Path) -> None:
        """Public discovery persists newly discovered servers for an IDP."""
        discovered = _cadc_server(
            name="Discovered-CADC",
            uri=AnyUrl("ivo://cadc.example/skaha"),
            url=AnyHttpUrl("https://cadc.example/skaha"),
        )
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.server._discover_for_idp", return_value=[discovered]),
            patch("canfar.server.Configuration", Configuration),
        ):
            servers = discover("cadc")

        assert servers == [discovered]
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            saved = Configuration()
        assert str(saved.get_server_by_uri("ivo://cadc.example/skaha").url) == (
            "https://cadc.example/skaha"
        )

    @pytest.mark.asyncio
    async def test_registry_retains_only_skaha_and_preferred_storage_records(
        self,
    ) -> None:
        """CADC discovery retains ARC despite Vault and preserves registry URLs."""
        registry = IVOARegistry(
            name="CADC",
            content=(
                "ivo://cadc.nrc.ca/skaha="
                "https://platform.example/skaha/capabilities\n"
                "ivo://cadc.nrc.ca/arc="
                "https://storage.example/custom/capabilities\n"
                "ivo://cadc.nrc.ca/vault="
                "https://storage.example/vault/capabilities\n"
                "ivo://other.example/arc="
                "https://platform.example/skaha-arc/capabilities"
            ),
        )
        search = IVOARegistrySearch(preferred_storage_leaf="arc")

        async with Discover(search) as discovery:
            resources = discovery.extract(registry)

        assert [(resource.uri, resource.url) for resource in resources] == [
            ("ivo://cadc.nrc.ca/skaha", "https://platform.example/skaha"),
            ("ivo://cadc.nrc.ca/arc", "https://storage.example/custom"),
            ("ivo://other.example/arc", "https://platform.example/skaha-arc"),
        ]

    def test_discover_refreshes_primary_storage_and_preserves_manual_entries(
        self,
        tmp_path: Path,
    ) -> None:
        """Rediscovery updates only the generated Storage Name entry."""
        manual = VOSpaceService(
            uri="ivo://cadc.nrc.ca/custom",
            url="https://manual.example/custom",
        )
        old_primary = VOSpaceService(
            uri="ivo://cadc.nrc.ca/arc",
            url="https://old.example/arc",
        )
        known = _cadc_server(
            name="canfar",
            storage={"canfar": old_primary, "archive": manual},
        )
        registry_body = "\n".join(
            (
                f"{_CADC_URI}={_CADC_URL}/capabilities",
                "ivo://cadc.nrc.ca/arc=https://storage.example/arc/capabilities",
                "ivo://cadc.nrc.ca/vault=https://storage.example/vault/capabilities",
            )
        )

        def registry_response(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                return httpx.Response(200, text=registry_body, request=request)
            return httpx.Response(200, request=request)

        session_capabilities = """
            <capabilities>
              <capability standardID="http://www.opencadc.org/std/platform#session-1">
                <interface>
                  <accessURL use="base">https://ws-uv.canfar.net/skaha/v1</accessURL>
                  <securityMethod
                    standardID="ivo://ivoa.net/sso#tls-with-certificate" />
                </interface>
              </capability>
            </capabilities>
        """

        def capabilities_response(request: httpx.Request) -> httpx.Response:
            content = (
                _VOSPACE_CAPABILITIES
                if str(request.url) == "https://storage.example/arc/capabilities"
                else session_capabilities
            )
            return httpx.Response(200, text=content, request=request)

        real_async_client = httpx.AsyncClient
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = _anonymous_config(known)
            with (
                patch(
                    "canfar.utils.discover.httpx.AsyncClient",
                    side_effect=lambda **_kwargs: real_async_client(
                        transport=httpx.MockTransport(registry_response)
                    ),
                ),
                patch(
                    "canfar.client.Client",
                    side_effect=_http_client_factory(
                        httpx.MockTransport(capabilities_response)
                    ),
                ),
            ):
                [discovered] = discover("cadc", config=config)

            persisted = Configuration().servers["canfar"]

        assert (
            discovered.storage
            == persisted.storage
            == {
                "canfar": VOSpaceService(
                    uri="ivo://cadc.nrc.ca/arc",
                    url="https://storage.example/arc",
                ),
                "archive": manual,
            }
        )

    @pytest.mark.parametrize("mode", ["missing", "malformed", "unreachable"])
    def test_storage_inspection_fail_or_keep_outcomes(
        self, mode: str, tmp_path: Path
    ) -> None:
        """Storage failures are kept non-strict and actionable when strict."""
        storage_resource = (
            None
            if mode == "missing"
            else DiscoveredServer(
                registry="CADC",
                uri="ivo://cadc.nrc.ca/arc",
                url="https://storage.example/arc",
            )
        )

        def response(request: httpx.Request) -> httpx.Response:
            if mode == "unreachable":
                message = "storage unavailable"
                raise httpx.ConnectError(message, request=request)
            return httpx.Response(200, text="<capabilities />", request=request)

        server = _cadc_server()
        transport = httpx.MockTransport(response)
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = _anonymous_config()
            with patch(
                "canfar.client.Client", side_effect=_http_client_factory(transport)
            ):
                assert (
                    enrich(
                        server,
                        config=config,
                        storage_resource=storage_resource,
                        strict=False,
                    )
                    == server
                )

            with (
                patch(
                    "canfar.client.Client",
                    side_effect=_http_client_factory(transport),
                ),
                pytest.raises(ServerFetchError, match="VOSpace Service") as exc_info,
            ):
                enrich(
                    server,
                    config=config,
                    storage_resource=storage_resource,
                    strict=True,
                )

        if mode == "malformed":
            assert isinstance(exc_info.value.__cause__, ValueError)

    def test_activation_freshly_inspects_storage_missing_during_discovery(self) -> None:
        """Activation obtains fresh evidence without transient Configuration state."""
        endpoint = DiscoveredServer(
            registry="CADC source",
            uri=_CADC_URI,
            url=_CADC_URL,
            status=200,
            name="CADC-CANFAR",
        )
        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(success=True, content="line")
        mock_discovery.extract = MagicMock(return_value=[endpoint])
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)
        session_capabilities = """
            <capabilities>
              <capability standardID="http://www.opencadc.org/std/platform#session-1">
                <interface>
                  <accessURL use="base">https://ws-uv.canfar.net/skaha/v1</accessURL>
                  <securityMethod
                    standardID="ivo://ivoa.net/sso#tls-with-certificate" />
                </interface>
              </capability>
            </capabilities>
        """
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                text=session_capabilities,
                request=request,
            )
        )
        config = _anonymous_config()

        with (
            patch("canfar.server.Discover", return_value=mock_discovery),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(transport),
            ),
        ):
            [discovered] = discover("cadc", config=config, save=False)
            reloaded = Configuration.model_validate(config.model_dump(mode="python"))
            with pytest.raises(
                ServerFetchError,
                match="same-namespace 'arc' registry record",
            ):
                activate("cadc", _CADC_URI, config=reloaded)

        assert discovered.version == "v1"
        assert discovered.storage == {}
        assert "_storage_discovery_errors" not in Configuration.__private_attributes__

    @pytest.mark.asyncio
    async def test_cross_registry_singletons_pair_by_namespace(self) -> None:
        """A lone same-environment fallback may cross registry provenance."""
        resources = [
            DiscoveredServer(
                registry="SRCNet",
                uri="ivo://canfar.net/src/skaha",
                url="https://one.example/skaha",
                status=200,
                name="canSRC",
            ),
            DiscoveredServer(
                registry="SRCNet",
                uri="ivo://swesrc.chalmers.se/skaha",
                url="https://two.example/skaha",
                status=200,
                name="sweSRC",
            ),
            DiscoveredServer(
                registry="SRCNet mirror B",
                uri="ivo://swesrc.chalmers.se/cavern",
                url="https://storage.example/two",
            ),
            DiscoveredServer(
                registry="SRCNet mirror A",
                uri="ivo://canfar.net/src/cavern",
                url="https://storage.example/one",
            ),
        ]
        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(success=True, content="line")
        mock_discovery.extract = MagicMock(return_value=resources)
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)

        def enriched(
            server: Server,
            *,
            storage_resource: DiscoveredServer,
            **_kwargs: object,
        ) -> Server:
            return server.model_copy(
                update={
                    "version": "v1",
                    "auths": ["oidc"],
                    "storage": {
                        server.name: VOSpaceService(
                            uri=storage_resource.uri,
                            url=storage_resource.url,
                        )
                    },
                },
                deep=True,
            )

        with (
            patch("canfar.server.Discover", return_value=mock_discovery),
            patch("canfar.server.enrich", side_effect=enriched),
        ):
            servers = await _discover_for_idp("srcnet")

        assert {
            server.name: str(server.storage[server.name].uri) for server in servers
        } == {
            "canSRC": "ivo://canfar.net/src/cavern",
            "sweSRC": "ivo://swesrc.chalmers.se/cavern",
        }

    def test_storage_pairing_never_crosses_prod_and_dev_sources(self) -> None:
        """A same-namespace record from another environment is not a fallback."""
        endpoint = DiscoveredServer(
            registry="https://registry.example/prod",
            development=False,
            uri="ivo://cadc.nrc.ca/skaha",
            url="https://platform.example/skaha",
            name="canfar",
        )
        dev_storage = DiscoveredServer(
            registry="https://registry.example/dev",
            development=True,
            uri="ivo://cadc.nrc.ca/arc",
            url="https://storage.example/arc",
        )

        assert _select_storage_resource(endpoint, [dev_storage], strict=False) is None

    def test_ambiguous_cross_registry_storage_is_not_last_write_wins(self) -> None:
        """Multiple namespace fallbacks are omitted or actionable, never arbitrary."""
        endpoint = DiscoveredServer(
            registry="https://registry.example/platform",
            uri="ivo://example.org/skaha",
            url="https://platform.example/skaha",
            name="example",
        )
        storage = [
            DiscoveredServer(
                registry=f"https://registry.example/storage-{index}",
                uri="ivo://example.org/cavern",
                url=f"https://storage-{index}.example/cavern",
            )
            for index in (1, 2)
        ]

        assert _select_storage_resource(endpoint, storage, strict=False) is None
        with pytest.raises(ServerFetchError, match="Multiple preferred VOSpace"):
            _select_storage_resource(endpoint, storage, strict=True)

    @pytest.mark.asyncio
    async def test_capability_enrichment_runs_concurrently_off_event_loop(
        self,
    ) -> None:
        """Blocking authenticated capability clients run in concurrent workers."""
        endpoints = [
            DiscoveredServer(
                registry="SRCNet",
                uri=f"ivo://site-{index}.example/skaha",
                url=f"https://site-{index}.example/skaha",
                status=200,
                name=f"site-{index}",
            )
            for index in (1, 2)
        ]
        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(
            success=True,
            content="line",
        )
        mock_discovery.extract = MagicMock(return_value=endpoints)
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)
        concurrent = Barrier(2, timeout=2)

        def convert(
            endpoint: DiscoveredServer,
            idp: str,
            **_kwargs: object,
        ) -> Server:
            concurrent.wait()
            return Server(
                idp=idp,
                name=endpoint.name,
                uri=AnyUrl(endpoint.uri),
                url=AnyHttpUrl(endpoint.url),
                version="v1",
                auths=["oidc"],
            )

        with (
            patch("canfar.server.Discover", return_value=mock_discovery),
            patch("canfar.server._discovered_to_server", side_effect=convert),
        ):
            servers = await _discover_for_idp("srcnet")

        assert [server.name for server in servers] == ["site-1", "site-2"]

    @pytest.mark.parametrize(
        "capabilities_case",
        [
            "empty",
            "malformed",
            "network",
            "non-success",
            "partial",
            "success",
            "timeout",
        ],
    )
    def test_discover_merges_only_complete_capability_metadata(
        self,
        tmp_path: Path,
        capabilities_case: str,
    ) -> None:
        """Discovery updates endpoint facts without replacing known optional data."""
        registry_url = "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
        registry_body = f"{_CADC_URI}={_CADC_URL}/capabilities"

        def registry_response(request: httpx.Request) -> httpx.Response:
            if request.method == "GET" and str(request.url) == registry_url:
                return httpx.Response(200, text=registry_body, request=request)
            if request.method == "HEAD" and str(request.url) == _CADC_URL:
                return httpx.Response(200, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        async_transport = httpx.MockTransport(registry_response)
        partial = """
            <capabilities>
              <capability standardID="http://www.opencadc.org/std/platform#session-2">
                <interface>
                  <accessURL use="base">https://ws-uv.canfar.net/skaha/v2</accessURL>
                </interface>
              </capability>
            </capabilities>
        """
        success = """
            <capabilities>
              <capability standardID="http://www.opencadc.org/std/platform#session-2">
                <interface>
                  <accessURL use="base">https://ws-uv.canfar.net/skaha/v2.1</accessURL>
                  <securityMethod standardID="ivo://ivoa.net/sso#token" />
                </interface>
              </capability>
            </capabilities>
        """

        def capabilities_response(request: httpx.Request) -> httpx.Response:
            if capabilities_case == "network":
                message = "connection refused"
                raise httpx.ConnectError(message, request=request)
            if capabilities_case == "timeout":
                message = "timed out"
                raise httpx.ReadTimeout(message, request=request)
            if capabilities_case == "non-success":
                return httpx.Response(503, request=request)
            content = {
                "empty": "",
                "malformed": "<capabilities>",
                "partial": partial,
                "success": success,
            }[capabilities_case]
            return httpx.Response(200, text=content, request=request)

        capabilities_transport = httpx.MockTransport(capabilities_response)
        real_async_client = httpx.AsyncClient
        known = _cadc_server(
            name="canfar",
            cores=8,
            ram=64,
            gpus=1,
            status="reachable",
        )
        config_path = tmp_path / "config.yaml"

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = _anonymous_config(known)
            config.save()

            with (
                patch(
                    "canfar.utils.discover.httpx.AsyncClient",
                    side_effect=lambda **_kwargs: real_async_client(
                        transport=async_transport,
                    ),
                ),
                patch(
                    "canfar.client.Client",
                    side_effect=_http_client_factory(capabilities_transport),
                ),
            ):
                discovered = discover("cadc", config=config)

            persisted = Configuration().servers["canfar"]

        expected = (
            known.model_copy(
                update={"version": "v2.1", "auths": ["oidc"]},
                deep=True,
            )
            if capabilities_case == "success"
            else known
        )
        assert discovered == [expected]
        assert config.servers["canfar"] == expected
        assert persisted == expected

    def test_activate_without_selector_requires_prompt_for_multiple_servers(
        self,
        tmp_path: Path,
    ) -> None:
        """Activation reports promptable choices when no selector can be inferred."""
        first = _cadc_server(name="First", uri=AnyUrl("ivo://first.example/skaha"))
        second = _cadc_server(
            name="Second",
            uri=AnyUrl("ivo://second.example/skaha"),
            url=AnyHttpUrl("https://second.example/skaha"),
        )
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, first, second)
            config.active = config.active.model_copy(update={"server": None})
            config.save()

            with (
                patch("canfar.server.Configuration", Configuration),
                pytest.raises(ServerSelectionRequiredError) as exc_info,
            ):
                activate("cadc")

        assert [server.name for server in exc_info.value.servers] == [
            "First",
            "Second",
        ]

    def test_discover_keys_named_server_by_registry_name(self, tmp_path: Path) -> None:
        """Discovery persists a registry-named server under that name key."""
        discovered = _cadc_server(
            name="Discovered-CADC",
            uri=AnyUrl("ivo://cadc.example/skaha"),
            url=AnyHttpUrl("https://cadc.example/skaha"),
        )
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.server._discover_for_idp", return_value=[discovered]),
            patch("canfar.server.Configuration", Configuration),
        ):
            discover("cadc")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            saved = Configuration()
        assert "Discovered-CADC" in saved.servers
        assert str(saved.servers["Discovered-CADC"].uri) == "ivo://cadc.example/skaha"

    def test_rediscovery_updates_existing_name_in_place(self, tmp_path: Path) -> None:
        """Re-discovering an existing Server Name updates it without duplicates."""
        first = _cadc_server(
            name="Discovered-CADC",
            uri=AnyUrl("ivo://cadc.example/skaha"),
            url=AnyHttpUrl("https://cadc.example/skaha"),
        )
        moved = first.model_copy(
            update={"url": AnyHttpUrl("https://cadc-moved.example/skaha")},
            deep=True,
        )
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.server.Configuration", Configuration),
        ):
            with patch("canfar.server._discover_for_idp", return_value=[first]):
                discover("cadc")
            with patch("canfar.server._discover_for_idp", return_value=[moved]):
                discover("cadc")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            saved = Configuration()
        names = [name for name, server in saved.servers.items() if server.idp == "cadc"]
        assert names.count("Discovered-CADC") == 1
        assert str(saved.servers["Discovered-CADC"].url) == (
            "https://cadc-moved.example/skaha"
        )

    def test_registry_rename_inserts_new_key_without_rewriting_old(
        self,
        tmp_path: Path,
    ) -> None:
        """A registry rename adds a new entry; the user's existing key survives."""
        original = _cadc_server(
            name="UserName",
            uri=AnyUrl("ivo://cadc.example/skaha"),
            url=AnyHttpUrl("https://cadc.example/skaha"),
        )
        renamed = original.model_copy(update={"name": "RegistryName"}, deep=True)
        config_path = tmp_path / "config.yaml"

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, original)
            config.save()

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.server._discover_for_idp", return_value=[renamed]),
            patch("canfar.server.Configuration", Configuration),
        ):
            discover("cadc")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            saved = Configuration()
        assert "UserName" in saved.servers
        assert "RegistryName" in saved.servers
        assert str(saved.servers["UserName"].uri) == "ivo://cadc.example/skaha"
        assert str(saved.servers["RegistryName"].uri) == "ivo://cadc.example/skaha"

    def test_discover_keys_unnamed_server_by_host_slug(self, tmp_path: Path) -> None:
        """Discovery persists unnamed registry endpoints under the host slug key."""
        endpoint = DiscoveredServer(
            registry="SRCNet",
            uri="ivo://swesrc.chalmers.se/skaha",
            url="https://swesrc.chalmers.se/skaha",
            status=200,
            name=None,
        )
        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(success=True, content="line")
        mock_discovery.extract = MagicMock(return_value=[endpoint])
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch("canfar.server.Discover", return_value=mock_discovery),
            patch(
                "canfar.server.enrich",
                side_effect=lambda item, **_kwargs: item.model_copy(
                    update={"version": "v1", "auths": ["oidc"]},
                    deep=True,
                ),
            ),
            patch("canfar.server.Configuration", Configuration),
        ):
            discover("srcnet")

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            saved = Configuration()
        assert "swesrc-chalmers-se" in saved.servers
        assert str(saved.servers["swesrc-chalmers-se"].uri) == (
            "ivo://swesrc.chalmers.se/skaha"
        )

    @pytest.mark.asyncio
    async def test_discover_for_idp_converts_active_endpoints(self) -> None:
        """Discovery converts reachable registry endpoints into HTTP server models."""
        endpoint = DiscoveredServer(
            registry="CADC",
            uri=_CADC_URI,
            url=_CADC_URL,
            status=200,
            name="CADC-CANFAR",
        )

        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(success=True, content="line")
        mock_discovery.extract = MagicMock(return_value=[endpoint])
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("canfar.server.Discover", return_value=mock_discovery),
            patch(
                "canfar.server.enrich",
                side_effect=lambda item, **_kwargs: item.model_copy(
                    update={"version": "v1", "auths": ["x509"]},
                    deep=True,
                ),
            ),
        ):
            servers = await _discover_for_idp("cadc")

        assert len(servers) == 1
        assert servers[0].idp == "cadc"
        assert str(servers[0].uri) == _CADC_URI

    def test_discovered_to_server_keeps_registry_metadata_when_capabilities_fail(
        self,
    ) -> None:
        """Malformed capabilities must not abort discovery for other servers."""
        endpoint = DiscoveredServer(
            registry="SRCNet",
            uri="ivo://example.org/skaha",
            url="https://broken.example.org/skaha",
            status=200,
            name="Broken",
        )
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                text="<capabilities>",
                request=request,
            )
        )

        with patch(
            "canfar.client.Client",
            side_effect=_http_client_factory(transport),
        ):
            server = _discovered_to_server(
                endpoint,
                "srcnet",
                config=_anonymous_config(idp="srcnet"),
            )

        assert server.idp == "srcnet"
        assert server.name == "Broken"
        assert str(server.url) == "https://broken.example.org/skaha"
        assert server.version is None

    def test_discovered_to_server_names_unnamed_endpoint_by_host_slug(self) -> None:
        """Endpoints without a registry name are named by their URI host slug."""
        endpoint = DiscoveredServer(
            registry="SRCNet",
            uri="ivo://swesrc.chalmers.se/skaha",
            url="https://swesrc.chalmers.se/skaha",
            status=200,
            name=None,
        )
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                503,
                request=request,
            )
        )

        with patch(
            "canfar.client.Client",
            side_effect=_http_client_factory(transport),
        ):
            server = _discovered_to_server(
                endpoint,
                "srcnet",
                config=_anonymous_config(idp="srcnet"),
            )

        assert server.name == "swesrc-chalmers-se"

    @pytest.mark.asyncio
    async def test_discover_for_idp_raises_when_registry_fetch_fails(self) -> None:
        """Registry fetch failures surface as ServerDiscoveryError."""
        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(
            success=False,
            error="connection refused",
        )
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("canfar.server.Discover", return_value=mock_discovery),
            pytest.raises(ServerDiscoveryError, match="Failed to discover"),
        ):
            await _discover_for_idp("cadc")

    @pytest.mark.asyncio
    async def test_discover_for_idp_honors_dev_sources_and_timeout(self) -> None:
        """Dev discovery includes dev registries and propagates request timeout."""
        mock_discovery = AsyncMock()
        mock_discovery.fetch.side_effect = [
            MagicMock(name="CADC", success=True, content="prod"),
            MagicMock(name="CADC@keel-dev", success=True, content="dev"),
        ]
        mock_discovery.extract = MagicMock(return_value=[])
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)

        with patch("canfar.server.Discover", return_value=mock_discovery) as factory:
            servers = await _discover_for_idp("cadc", dev=True, timeout=11)

        assert servers == []
        search = factory.call_args.args[0]
        assert (
            "https://rc-ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"
            in search.registries
        )
        assert factory.call_args.kwargs["timeout"] == 11
        assert mock_discovery.extract.call_args.kwargs["dev"] is True


class TestServerModelFields:
    """Tests for extended Server resource fields."""

    def test_server_accepts_resource_fields(self) -> None:
        """Server models accept cores, ram, and gpus."""
        server = _cadc_server(
            cores=16,
            ram=192,
            gpus=4,
        )

        assert server.cores == 16
        assert server.ram == 192
        assert server.gpus == 4

    def test_server_resource_defaults(self) -> None:
        """Server models apply default resource settings without enrichment."""
        server = _cadc_server()

        assert server.cores == 2
        assert server.ram == 16
        assert server.gpus == 0

    def test_server_discovery_error_exposes_structured_code(self) -> None:
        """Discovery errors carry stable structured error codes."""
        error = ServerDiscoveryError("none found", code=ErrorCode.SERVER_NONE_AVAILABLE)

        assert error.code == ErrorCode.SERVER_NONE_AVAILABLE
        assert error.structured.code == "server.none_available"
