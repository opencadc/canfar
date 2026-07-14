"""Behavior tests for the server selection and discovery seam."""

from __future__ import annotations

from pathlib import Path
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
from canfar.models.http import Server
from canfar.models.registry import Server as DiscoveredServer
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    ServerSelectionRequiredError,
    _discover_for_idp,
    _discovered_to_server,
    activate,
    discover,
    use,
)
from canfar.server import (
    list_servers as server_list,
)
from tests.helpers.config import assign_servers

if TYPE_CHECKING:
    from collections.abc import Callable

_CADC_URI = "ivo://cadc.nrc.ca/skaha"
_CADC_URL = "https://ws-uv.canfar.net/skaha"


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
