"""Behavior tests for the server selection and discovery seam."""

from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
from threading import Barrier
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call, patch

import httpx2
import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl

from canfar._server_discovery import (
    _discover_for_idp,
    _discovered_to_server,
)
from canfar.errors import ErrorCode
from canfar.models.active import ActiveConfig
from canfar.models.auth import OIDCCredential, RuntimeCredential, X509Credential
from canfar.models.config import Configuration
from canfar.models.http import (
    ResourceRange,
    Server,
    ServerResources,
    SessionResources,
    VOSpaceService,
)
from canfar.models.registry import (
    ContainerRegistry,
    IVOARegistry,
    ServerProbe,
)
from canfar.models.registry import Server as DiscoveredServer
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    ServerSelectionRequiredError,
    activate,
    discover,
    enrich,
    use,
)
from canfar.server import (
    __all__ as server_exports,
)
from canfar.server import (
    list_servers as server_list,
)
from canfar.utils import discover as registry_discovery
from canfar.utils.registry import RegistryEvidenceError, select_storage
from tests.helpers.config import assign_servers

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractContextManager

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


def test_public_exports_declare_server_api() -> None:
    """The module's public and compatibility exports remain explicit."""
    expected = {
        "ServerActivation",
        "ServerDiscoveryError",
        "ServerFetchError",
        "ServerSelectionRequiredError",
        "ServerSelectorError",
        "activate",
        "activate_authentication",
        "discover",
        "enrich",
        "list_servers",
        "use",
    }

    assert set(server_exports) == expected


def test_enrich_preserves_storage_resource_annotation() -> None:
    """The public enrichment signature retains its released annotation text."""
    annotation = inspect.signature(enrich).parameters["storage_resource"].annotation

    assert annotation == "RegistryResource | None | object"


def _http_client_factory(
    transport: httpx2.BaseTransport,
) -> Callable[..., httpx2.Client]:
    """Return an HTTPX2 client factory bound to a test transport."""
    client_type = httpx2.Client
    return lambda **kwargs: client_type(transport=transport, **kwargs)


_RESOURCES = ServerResources(
    flexible=SessionResources(
        cores=ResourceRange(min=1, max=16),
        ram=ResourceRange(min=4, max=32),
    ),
    fixed=SessionResources(
        cores=ResourceRange(min=1, max=16),
        ram=ResourceRange(min=1, max=192),
    ),
    gpus=ResourceRange(min=1, max=4),
    sessions=5,
)


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


def _use_discovery(stub: AsyncMock) -> AbstractContextManager[object]:
    """Route registry fetch, extract, and check through one test double."""

    async def fetch(_http: object, *args: object, **kwargs: object) -> object:
        return await stub.fetch(*args, **kwargs)

    def extract(registry: object, *, leaf: str | None, dev: bool = False) -> object:
        del leaf
        return stub.extract(registry, dev=dev)

    async def check(_http: object, endpoint: object) -> object:
        return await stub.check(endpoint)

    return patch.multiple(
        "canfar.utils.discover", fetch=fetch, extract=extract, check=check
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
            config.editor.save()

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

    def test_discover_uses_editor_for_server_state_and_persistence(
        self,
        tmp_path: Path,
    ) -> None:
        """Discovery updates and persists Servers through the editor boundary."""
        discovered = _cadc_server(name="Discovered-CADC")
        config_path = tmp_path / "config.yaml"

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar._server_discovery._discover_for_idp",
                return_value=[discovered],
            ),
        ):
            config = _anonymous_config()
            discover("cadc", config=config)

            assert config.servers["Discovered-CADC"] == discovered
            assert Configuration().servers["Discovered-CADC"] == discovered


class TestServerUse:
    """Tests for canfar.server.use()."""

    def test_activate_uses_editor_for_active_selection_and_history(
        self,
        tmp_path: Path,
    ) -> None:
        """Activation records a Server Name through the editor boundary."""
        target = _cadc_server(name="Selected-CADC")
        fetched = target.model_copy(update={"resources": _RESOURCES}, deep=True)
        config_path = tmp_path / "config.yaml"

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = _anonymous_config(target)
            config.editor.save()

            with patch("canfar.server._validate_server", return_value=fetched):
                activation = activate("cadc", "Selected-CADC", config=config)

            assert activation.server == fetched
            assert config.active.server == "Selected-CADC"
            assert config.active.servers["cadc"] == "Selected-CADC"
            saved = Configuration()

        assert saved.active.server == "Selected-CADC"
        assert saved.active.servers["cadc"] == "Selected-CADC"

    def test_activate_resolves_remembered_selection_by_server_name(
        self,
        tmp_path: Path,
    ) -> None:
        """Remembered Server Selection is resolved by Server Name, not URI."""
        first = _cadc_server(name="First", uri=AnyUrl("ivo://first.example/skaha"))
        remembered = _cadc_server(
            name="Remembered",
            uri=AnyUrl("ivo://remembered.example/skaha"),
        )
        config_path = tmp_path / "config.yaml"

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration(
                active=ActiveConfig(
                    authentication="cadc",
                    server=None,
                    servers={"cadc": "Remembered"},
                ),
                authentication={"cadc": X509Credential(idp="cadc")},
                servers={first.name: first, remembered.name: remembered},
            )

            with patch("canfar.server._validate_server", return_value=remembered):
                activation = activate("cadc", config=config)

        assert activation.reason == "remembered"
        assert activation.server.name == "Remembered"
        assert config.active.server == "Remembered"
        assert config.active.servers["cadc"] == "Remembered"

    def test_use_by_uri_updates_active_server(self, tmp_path: Path) -> None:
        """Selecting by URI fetches, validates, and saves the active server."""
        target = _cadc_server()
        fetched = target.model_copy(update={"resources": _RESOURCES}, deep=True)
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, target)
            config.editor.save()

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
        fetched = target.model_copy(update={"resources": _RESOURCES}, deep=True)
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, target)
            config.editor.save()

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
            config.editor.save()
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
        fetched = discovered.model_copy(update={"resources": _RESOURCES}, deep=True)
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            assign_servers(config, known)
            config.editor.save()

            def merge_discovered(
                _idp: str,
                *,
                config: Configuration,
                **_kwargs: object,
            ) -> list[Server]:
                config.editor.set(f"servers.{discovered.name}", discovered)
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
            config.editor.save()
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
            config.editor.save()
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
                "canfar._server_discovery._discover_for_idp",
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
            patch(
                "canfar._server_discovery._discover_for_idp",
                return_value=[discovered],
            ),
            patch("canfar.server.Configuration", Configuration),
        ):
            servers = discover("cadc")

        assert servers == [discovered]
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            saved = Configuration()
        assert str(
            next(
                server
                for server in saved.servers.values()
                if str(server.uri) == "ivo://cadc.example/skaha"
            ).url
        ) == ("https://cadc.example/skaha")

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
        resources = registry_discovery.extract(registry, leaf="arc")

        assert [(resource.uri, resource.url) for resource in resources] == [
            ("ivo://cadc.nrc.ca/skaha", "https://platform.example/skaha"),
            ("ivo://cadc.nrc.ca/arc", "https://storage.example/custom"),
            ("ivo://other.example/arc", "https://platform.example/skaha-arc"),
        ]

    def test_discover_refreshes_primary_storage_and_preserves_manual_entries(
        self,
        tmp_path: Path,
    ) -> None:
        """Rediscovery updates only the generated Storage Identifier entry."""
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

        def registry_response(request: httpx2.Request) -> httpx2.Response:
            if request.method == "GET":
                return httpx2.Response(200, text=registry_body, request=request)
            return httpx2.Response(200, request=request)

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

        def capabilities_response(request: httpx2.Request) -> httpx2.Response:
            content = (
                _VOSPACE_CAPABILITIES
                if str(request.url) == "https://storage.example/arc/capabilities"
                else session_capabilities
            )
            return httpx2.Response(200, text=content, request=request)

        real_async_client = httpx2.AsyncClient
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = _anonymous_config(known)
            with (
                patch(
                    "canfar.utils.discover.AsyncClient",
                    side_effect=lambda **_kwargs: real_async_client(
                        transport=httpx2.MockTransport(registry_response)
                    ),
                ),
                patch(
                    "canfar.client.Client",
                    side_effect=_http_client_factory(
                        httpx2.MockTransport(capabilities_response)
                    ),
                ),
            ):
                [discovered] = discover("cadc", config=config)

            persisted = Configuration().servers["canfar"]

        assert discovered.storage == persisted.storage
        assert set(discovered.storage) == {"canfar", "archive"}
        assert discovered.storage["canfar"] == VOSpaceService(
            uri="ivo://cadc.nrc.ca/arc",
            url="https://storage.example/arc",
        )
        assert discovered.storage["archive"] == manual

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

        def response(request: httpx2.Request) -> httpx2.Response:
            if mode == "unreachable":
                message = "storage unavailable"
                raise httpx2.ConnectError(message, request=request)
            return httpx2.Response(200, text="<capabilities />", request=request)

        server = _cadc_server()
        transport = httpx2.MockTransport(response)
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
        transport = httpx2.MockTransport(
            lambda request: httpx2.Response(
                200,
                text=session_capabilities,
                request=request,
            )
        )
        config = _anonymous_config()

        with (
            _use_discovery(mock_discovery),
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

        def with_storage(
            server: Server,
            *,
            storage_resource: DiscoveredServer,
            **_kwargs: object,
        ) -> Server:
            return server.model_copy(
                update={
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
            _use_discovery(mock_discovery),
            patch(
                "canfar._server_discovery._enrich_storage",
                side_effect=with_storage,
            ),
            patch(
                "canfar._server_discovery.enrich",
                side_effect=lambda server, **_kwargs: server.model_copy(
                    update={"version": "v1", "auths": ["oidc"]},
                    deep=True,
                ),
            ),
            patch(
                "canfar._server_discovery._fetch_resources",
                side_effect=lambda server, **_kwargs: server,
            ),
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

        assert select_storage(endpoint, [dev_storage], strict=False) is None

    @pytest.mark.asyncio
    async def test_mixed_registry_records_keep_per_record_environment(self) -> None:
        """Development-looking records stay isolated within a production source."""
        registry = IVOARegistry(
            name="SRCNet",
            source="https://registry.example/resources",
            content=(
                "ivo://example.org/skaha="
                "https://platform.example/skaha/capabilities\n"
                "ivo://example.org/cavern="
                "https://storage.example/dev/capabilities"
            ),
        )
        endpoint, storage = registry_discovery.extract(
            registry, leaf="cavern", dev=True
        )

        assert endpoint.development is False
        assert storage.development is True
        assert select_storage(endpoint, [storage], strict=False) is None

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

        assert select_storage(endpoint, storage, strict=False) is None
        with pytest.raises(RegistryEvidenceError, match="Multiple preferred VOSpace"):
            select_storage(endpoint, storage, strict=True)

    @pytest.mark.asyncio
    async def test_capability_enrichment_runs_concurrently_off_event_loop(
        self,
    ) -> None:
        """Workers run concurrently with isolated, pre-materialized config copies."""
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
        worker_configs: list[Configuration] = []
        config = Configuration(
            active=ActiveConfig(authentication="srcnet", server=None),
            authentication={"srcnet": OIDCCredential(idp="srcnet")},
            servers={},
        )

        def convert(
            endpoint: DiscoveredServer,
            idp: str,
            **kwargs: object,
        ) -> tuple[Server, ServerProbe]:
            worker_config = kwargs["config"]
            assert isinstance(worker_config, Configuration)
            worker_configs.append(worker_config)
            assert kwargs["token"] == "current-token"
            assert kwargs["certificate"] is None
            concurrent.wait()
            server = Server(
                idp=idp,
                name=endpoint.name,
                uri=AnyUrl(endpoint.uri),
                url=AnyHttpUrl(endpoint.url),
                version="v1",
                auths=["oidc"],
            )
            probe = ServerProbe(
                name=str(endpoint.name),
                uri=endpoint.uri,
                url=endpoint.url,
                status="connected",
            )
            return server, probe

        materialize = AsyncMock(return_value=RuntimeCredential(token="current-token"))
        with (
            _use_discovery(mock_discovery),
            patch(
                "canfar._server_discovery._discovered_to_server",
                side_effect=convert,
            ),
            patch(
                "canfar.client.HTTPClient._materialize_credentials",
                new=materialize,
            ),
        ):
            servers = await _discover_for_idp("srcnet", config=config)

        assert [server.name for server in servers] == ["site-1", "site-2"]
        materialize.assert_awaited_once_with()
        assert len({id(worker_config) for worker_config in worker_configs}) == 2
        assert all(worker_config is not config for worker_config in worker_configs)

    @pytest.mark.asyncio
    async def test_worker_requests_use_pre_materialized_runtime_token(self) -> None:
        """Fan-out requests cannot invoke saved-record refresh or persistence."""
        endpoint = DiscoveredServer(
            registry="SRCNet",
            uri="ivo://site.example/skaha",
            url="https://site.example/skaha",
            status=200,
            name="site",
        )
        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(success=True, content="line")
        mock_discovery.extract = MagicMock(return_value=[endpoint])
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)
        config = Configuration(
            active=ActiveConfig(authentication="srcnet", server=None),
            authentication={"srcnet": OIDCCredential(idp="srcnet")},
            servers={},
        )
        requests: list[httpx2.Request] = []
        session_capabilities = """
            <capabilities>
              <capability standardID="http://www.opencadc.org/std/platform#session-1">
                <interface>
                  <accessURL use="base">https://site.example/skaha/v1</accessURL>
                  <securityMethod standardID="ivo://ivoa.net/sso#token" />
                </interface>
              </capability>
            </capabilities>
        """

        def response(request: httpx2.Request) -> httpx2.Response:
            requests.append(request)
            if request.url.path.endswith("/context"):
                return httpx2.Response(
                    200, json={"maxInteractiveSessions": 3}, request=request
                )
            return httpx2.Response(200, text=session_capabilities, request=request)

        materialize = AsyncMock(return_value=RuntimeCredential(token="runtime-token"))
        with (
            _use_discovery(mock_discovery),
            patch(
                "canfar.client.HTTPClient._materialize_credentials",
                new=materialize,
            ),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx2.MockTransport(response)),
            ),
            patch("canfar.auth.oidc.sync_refresh") as refresh,
        ):
            [server] = await _discover_for_idp("srcnet", config=config)

        assert server.version == "v1"
        assert server.resources == ServerResources(sessions=3)
        materialize.assert_awaited_once_with()
        refresh.assert_not_called()
        assert [
            (request.url.path, request.headers["Authorization"]) for request in requests
        ] == [
            ("/skaha/capabilities", "Bearer runtime-token"),
            ("/skaha/v1/context", "Bearer runtime-token"),
        ]

    @pytest.mark.asyncio
    async def test_environment_token_materializes_without_saved_credential(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Environment bearer auth survives preparation and worker fan-out."""
        endpoint = DiscoveredServer(
            registry="SRCNet",
            uri="ivo://site.example/skaha",
            url="https://site.example/skaha",
            status=200,
            name="site",
        )
        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(success=True, content="line")
        mock_discovery.extract = MagicMock(return_value=[endpoint])
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)
        requests: list[httpx2.Request] = []
        session_capabilities = """
            <capabilities>
              <capability standardID="http://www.opencadc.org/std/platform#session-1">
                <interface>
                  <accessURL use="base">https://site.example/skaha/v1</accessURL>
                  <securityMethod standardID="ivo://ivoa.net/sso#token" />
                </interface>
              </capability>
            </capabilities>
        """

        def response(request: httpx2.Request) -> httpx2.Response:
            requests.append(request)
            return httpx2.Response(200, text=session_capabilities, request=request)

        monkeypatch.delenv("CANFAR_CERTIFICATE", raising=False)
        monkeypatch.setenv("CANFAR_TOKEN", "environment-token")
        with (
            _use_discovery(mock_discovery),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(httpx2.MockTransport(response)),
            ),
        ):
            [server] = await _discover_for_idp(
                "srcnet",
                config=_anonymous_config(idp="srcnet"),
            )

        assert server.version == "v1"
        assert [
            (request.url.path, request.headers["Authorization"]) for request in requests
        ] == [
            ("/skaha/capabilities", "Bearer environment-token"),
            ("/skaha/v1/context", "Bearer environment-token"),
        ]

    @pytest.mark.asyncio
    async def test_environment_certificate_materializes_without_saved_credential(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Environment certificate auth survives preparation and worker fan-out."""
        endpoint = DiscoveredServer(
            registry="SRCNet",
            uri="ivo://site.example/skaha",
            url="https://site.example/skaha",
            status=200,
            name="site",
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
                  <accessURL use="base">https://site.example/skaha/v1</accessURL>
                  <securityMethod
                    standardID="ivo://ivoa.net/sso#tls-with-certificate" />
                </interface>
              </capability>
            </capabilities>
        """
        certificate = tmp_path / "environment.pem"
        valid = MagicMock(return_value=certificate.as_posix())
        ssl_context = MagicMock()

        monkeypatch.delenv("CANFAR_TOKEN", raising=False)
        monkeypatch.setenv("CANFAR_CERTIFICATE", certificate.as_posix())
        with (
            _use_discovery(mock_discovery),
            patch(
                "canfar.client.x509.inspect",
                return_value={
                    "path": certificate.as_posix(),
                    "expiry": 9_999_999_999.0,
                },
            ),
            patch("canfar.client.x509.valid", new=valid),
            patch(
                "canfar.client.HTTPClient._get_ssl_context",
                return_value=ssl_context,
            ) as get_ssl_context,
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(
                    httpx2.MockTransport(
                        lambda request: httpx2.Response(
                            200,
                            text=session_capabilities,
                            request=request,
                        )
                    )
                ),
            ),
        ):
            [server] = await _discover_for_idp(
                "srcnet",
                config=_anonymous_config(idp="srcnet"),
            )

        assert server.version == "v1"
        valid.assert_called_once_with(certificate)
        assert get_ssl_context.call_args_list == [call(certificate), call(certificate)]

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
        registry_url = "https://cadc-west-01.canfar.net/reg/resource-caps"
        registry_body = f"{_CADC_URI}={_CADC_URL}/capabilities"

        def registry_response(request: httpx2.Request) -> httpx2.Response:
            if request.method == "GET" and str(request.url) == registry_url:
                return httpx2.Response(200, text=registry_body, request=request)
            if request.method == "HEAD" and str(request.url) == _CADC_URL:
                return httpx2.Response(200, request=request)
            message = f"Unexpected request: {request.method} {request.url}"
            raise AssertionError(message)

        async_transport = httpx2.MockTransport(registry_response)
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

        def capabilities_response(request: httpx2.Request) -> httpx2.Response:
            if capabilities_case == "network":
                message = "connection refused"
                raise httpx2.ConnectError(message, request=request)
            if capabilities_case == "timeout":
                message = "timed out"
                raise httpx2.ReadTimeout(message, request=request)
            if capabilities_case == "non-success":
                return httpx2.Response(503, request=request)
            content = {
                "empty": "",
                "malformed": "<capabilities>",
                "partial": partial,
                "success": success,
            }[capabilities_case]
            return httpx2.Response(200, text=content, request=request)

        capabilities_transport = httpx2.MockTransport(capabilities_response)
        real_async_client = httpx2.AsyncClient
        known = _cadc_server(name="canfar", resources=_RESOURCES)
        config_path = tmp_path / "config.yaml"

        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = _anonymous_config(known)
            config.editor.save()

            with (
                patch(
                    "canfar.utils.discover.AsyncClient",
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
            config.editor.save()

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
            patch(
                "canfar._server_discovery._discover_for_idp",
                return_value=[discovered],
            ),
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
            with patch(
                "canfar._server_discovery._discover_for_idp",
                return_value=[first],
            ):
                discover("cadc")
            with patch(
                "canfar._server_discovery._discover_for_idp",
                return_value=[moved],
            ):
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
            config.editor.save()

        with (
            patch("canfar.models.config.CONFIG_PATH", config_path),
            patch(
                "canfar._server_discovery._discover_for_idp",
                return_value=[renamed],
            ),
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
            _use_discovery(mock_discovery),
            patch(
                "canfar._server_discovery.enrich",
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
            _use_discovery(mock_discovery),
            patch(
                "canfar._server_discovery.enrich",
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
        transport = httpx2.MockTransport(
            lambda request: httpx2.Response(
                200,
                text="<capabilities>",
                request=request,
            )
        )

        with patch(
            "canfar.client.Client",
            side_effect=_http_client_factory(transport),
        ):
            server, probe = _discovered_to_server(
                endpoint,
                "srcnet",
                config=_anonymous_config(idp="srcnet"),
            )

        assert server.idp == "srcnet"
        assert server.name == "Broken"
        assert str(server.url) == "https://broken.example.org/skaha"
        assert server.version is None
        assert (probe.name, probe.status) == ("Broken", "error")

    def test_discovered_to_server_names_unnamed_endpoint_by_host_slug(self) -> None:
        """Endpoints without a registry name are named by their URI host slug."""
        endpoint = DiscoveredServer(
            registry="SRCNet",
            uri="ivo://swesrc.chalmers.se/skaha",
            url="https://swesrc.chalmers.se/skaha",
            status=200,
            name=None,
        )
        transport = httpx2.MockTransport(
            lambda request: httpx2.Response(
                503,
                request=request,
            )
        )

        with patch(
            "canfar.client.Client",
            side_effect=_http_client_factory(transport),
        ):
            server, probe = _discovered_to_server(
                endpoint,
                "srcnet",
                config=_anonymous_config(idp="srcnet"),
            )

        assert server.name == "swesrc-chalmers-se"
        assert (probe.name, probe.status) == ("swesrc-chalmers-se", "error")

    @pytest.mark.asyncio
    async def test_discover_for_idp_raises_when_registry_fetch_fails(self) -> None:
        """Registry fetch failures surface as ServerDiscoveryError."""
        failed = IVOARegistry(
            name="CADC", content="", success=False, error="connection refused"
        )

        with (
            patch("canfar.utils.discover.fetch", AsyncMock(return_value=failed)),
            pytest.raises(ServerDiscoveryError, match="Failed to discover"),
        ):
            await _discover_for_idp("cadc")

    @pytest.mark.asyncio
    async def test_discover_for_idp_honors_dev_sources_and_timeout(self) -> None:
        """Dev discovery includes dev registries and propagates request timeout."""
        fetch = AsyncMock(
            side_effect=[
                IVOARegistry(name="CADC", content="prod"),
                IVOARegistry(name="CADC@keel-dev", content="dev"),
            ]
        )

        with (
            patch(
                "canfar.utils.discover.client", wraps=registry_discovery.client
            ) as client,
            patch("canfar.utils.discover.fetch", fetch),
            patch("canfar.utils.discover.extract", return_value=[]) as extract,
        ):
            servers = await _discover_for_idp("cadc", dev=True, timeout=11)

        assert servers == []
        assert "https://rc-ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps" in [
            call.args[1] for call in fetch.call_args_list
        ]
        client.assert_called_once_with(11)
        assert extract.call_args.kwargs["dev"] is True


class TestDiscoveryOutcomes:
    """Discovery reports why each Science Platform Server is usable or not."""

    def test_discover_reports_each_outcome_and_reads_resources(
        self,
        tmp_path: Path,
    ) -> None:
        """Probe, capability, and context replies map to one outcome per Server."""
        registry_url = "https://cadc-west-01.canfar.net/reg/resource-caps"
        hosts = ("ok", "slow", "down", "broken", "late", "refused", "denied")
        registry_body = "\n".join(
            f"ivo://{host}.example/skaha=https://{host}.example/skaha/capabilities"
            for host in hosts
        )

        def registry_response(request: httpx2.Request) -> httpx2.Response:
            if request.method == "GET" and str(request.url) == registry_url:
                return httpx2.Response(200, text=registry_body, request=request)
            if request.url.host == "slow.example":
                message = "timed out"
                raise httpx2.ConnectTimeout(message, request=request)
            if request.url.host == "down.example":
                message = "name not resolved"
                raise httpx2.ConnectError(message, request=request)
            if request.url.host == "broken.example":
                return httpx2.Response(503, request=request)
            return httpx2.Response(200, request=request)

        platform_requests: list[httpx2.Request] = []

        def platform_response(request: httpx2.Request) -> httpx2.Response:
            platform_requests.append(request)
            if request.url.host == "late.example":
                message = "timed out"
                raise httpx2.ReadTimeout(message, request=request)
            if request.url.host == "refused.example":
                message = "connection refused"
                raise httpx2.ConnectError(message, request=request)
            if request.url.host == "denied.example":
                return httpx2.Response(403, request=request)
            if request.url.path.endswith("/context"):
                return httpx2.Response(
                    200,
                    json={
                        "cores": {
                            "defaultRequest": 1,
                            "defaultLimit": 2,
                            "options": [1, 2, 4],
                        },
                        "maxInteractiveSessions": 3,
                    },
                    request=request,
                )
            capabilities = f"""
                <capabilities>
                  <capability
                    standardID="http://www.opencadc.org/std/platform#session-1">
                    <interface>
                      <accessURL use="base">https://{request.url.host}/skaha/v1</accessURL>
                      <securityMethod standardID="ivo://ivoa.net/sso#token" />
                    </interface>
                  </capability>
                </capabilities>
            """
            return httpx2.Response(200, text=capabilities, request=request)

        probes: list[ServerProbe] = []
        real_async_client = httpx2.AsyncClient
        with (
            patch("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml"),
            patch(
                "canfar.utils.discover.AsyncClient",
                side_effect=lambda **_kwargs: real_async_client(
                    transport=httpx2.MockTransport(registry_response),
                ),
            ),
            patch(
                "canfar.client.Client",
                side_effect=_http_client_factory(
                    httpx2.MockTransport(platform_response)
                ),
            ),
        ):
            config = _anonymous_config()
            config.editor.set(
                "registry",
                ContainerRegistry(username="user", secret="registry-secret"),
            )
            with patch("canfar._server_discovery.log") as log:
                servers = discover(
                    "cadc", config=config, save=False, on_probe=probes.append
                )

        assert {probe.name: probe.status for probe in probes} == {
            "ok-example": "connected",
            "slow-example": "timeout",
            "down-example": "unreachable",
            "broken-example": "error",
            "late-example": "timeout",
            "refused-example": "unreachable",
            "denied-example": "error",
        }
        names = [probe.name for probe in probes]
        assert [probe.status for probe in probes[:7]] == ["pending"] * 7
        assert sorted(names[:7]) == sorted(names[7:])
        outcomes = {probe.name: probe for probe in probes[7:]}
        assert outcomes["broken-example"].detail == (
            "HTTP 503 from https://broken.example/skaha"
        )
        reasons = [
            call.args[1:3]
            for call in log.debug.call_args_list
            if call.args[0] == "Server %s %s: %s"
        ]
        assert sorted(reasons) == sorted(
            (probe.name, probe.status)
            for probe in outcomes.values()
            if probe.status != "connected"
        )
        [server] = servers
        assert server.name == "ok-example"
        assert server.resources == ServerResources(
            flexible=SessionResources(cores=ResourceRange(min=1, max=2)),
            fixed=SessionResources(cores=ResourceRange(min=1, max=4)),
            sessions=3,
        )
        assert config.servers["ok-example"].resources == server.resources
        assert all(
            "X-Skaha-Registry-Auth" not in request.headers
            for request in platform_requests
        )

    @pytest.mark.asyncio
    async def test_one_slow_endpoint_does_not_delay_the_others(self) -> None:
        """A reachable Server is inspected while another check is still waiting."""
        endpoints = [
            DiscoveredServer(
                registry="SRCNet",
                uri=f"ivo://{host}.example/skaha",
                url=f"https://{host}.example/skaha",
                name=host,
            )
            for host in ("slow", "fast")
        ]
        released = asyncio.Event()

        async def check(endpoint: DiscoveredServer) -> DiscoveredServer:
            if endpoint.name == "slow":
                await released.wait()
                endpoint.failure = "timeout"
            else:
                endpoint.status = 200
            return endpoint

        def inspect(
            endpoint: DiscoveredServer, idp: str, **_kwargs: object
        ) -> tuple[Server, ServerProbe]:
            probe = ServerProbe(
                name="fast", uri=endpoint.uri, url=endpoint.url, status="connected"
            )
            return _cadc_server(name="fast", idp=idp), probe

        def on_probe(probe: ServerProbe) -> None:
            if probe.status == "connected":
                released.set()

        mock_discovery = AsyncMock()
        mock_discovery.fetch.return_value = MagicMock(success=True, content="line")
        mock_discovery.extract = MagicMock(return_value=endpoints)
        mock_discovery.check = AsyncMock(side_effect=check)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)
        with (
            _use_discovery(mock_discovery),
            patch(
                "canfar._server_discovery._discovered_to_server",
                side_effect=inspect,
            ),
        ):
            servers = await asyncio.wait_for(
                _discover_for_idp(
                    "srcnet",
                    config=_anonymous_config(idp="srcnet"),
                    on_probe=on_probe,
                ),
                timeout=5,
            )

        assert [server.name for server in servers] == ["fast"]


class TestServerModelFields:
    """Tests for extended Server resource fields."""

    def test_server_accepts_session_resources(self) -> None:
        """Server models carry advertised Session resource limits."""
        server = _cadc_server(resources=_RESOURCES)

        assert server.resources == _RESOURCES

    def test_server_resources_are_unknown_without_enrichment(self) -> None:
        """Server models do not invent limits a Server never advertised."""
        assert _cadc_server().resources is None

    @pytest.mark.parametrize("field", ["cores", "ram", "gpus"])
    def test_server_rejects_retired_resource_fields(self, field: str) -> None:
        """Retired flat limits are not accepted in place of ``resources``."""
        with pytest.raises(ValueError, match="Extra inputs are not permitted"):
            _cadc_server(**{field: 4})

    def test_server_discovery_error_exposes_structured_code(self) -> None:
        """Discovery errors carry stable structured error codes."""
        error = ServerDiscoveryError("none found", code=ErrorCode.SERVER_NONE_AVAILABLE)

        assert error.code == ErrorCode.SERVER_NONE_AVAILABLE
        assert ServerFetchError("unreachable").code == ErrorCode.TRANSPORT_FAILURE
