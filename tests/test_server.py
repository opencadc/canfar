"""Behavior tests for the server selection and fetch seam."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml
from pydantic import AnyHttpUrl, AnyUrl

from canfar.errors import ErrorCode
from canfar.models.auth import OIDCCredential, X509Credential
from canfar.models.config import Configuration
from canfar.models.http import Server
from canfar.models.registry import Server as DiscoveredServer
from canfar.server import (
    ServerDiscoveryError,
    ServerFetchError,
    ServerSelectorError,
    _discover_for_idp,
    _discovered_to_server,
    _enrich_from_capabilities,
    _validate_server,
    use,
)
from canfar.server import (
    list_servers as server_list,
)

_CADC_URI = "ivo://cadc.nrc.ca/skaha"
_CADC_URL = "https://ws-uv.canfar.net/skaha"
_CONTEXT_PAYLOAD = {
    "cores": {"defaultLimit": 16, "options": [1, 2, 4, 8, 16]},
    "memoryGB": {"defaultLimit": 192, "options": [1, 2, 4, 8, 16, 32, 64, 128, 192]},
    "gpus": {"options": [0, 1, 2, 4]},
}


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
            config.server = [cadc, srcnet]
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
            config.authentication = [
                X509Credential(idp="cadc", path=Path.home() / ".ssl" / "cadcproxy.pem"),
                OIDCCredential(idp="srcnet"),
            ]
            config.server = [cadc]
            config.active = config.active.model_copy(
                update={"authentication": "srcnet", "server": cadc.uri}
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
            config.server = [target]
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
            assert str(saved.active.server) == _CADC_URI
            mock_validate.assert_called_once()

    def test_use_by_unique_name_updates_active_server(self, tmp_path: Path) -> None:
        """Selecting by unique display name resolves and saves."""
        target = _cadc_server(name="CADC-CANFAR")
        fetched = target.model_copy(update={"cores": 8, "ram": 64}, deep=True)
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.server = [target]
            config.save()

            with (
                patch("canfar.server._validate_server", return_value=fetched),
                patch("canfar.server.Configuration", Configuration),
            ):
                use("CADC-CANFAR")

            saved = Configuration()
            assert str(saved.active.server) == _CADC_URI

    def test_use_ambiguous_name_fails_with_uri_guidance(self, tmp_path: Path) -> None:
        """Ambiguous names fail without changing active server."""
        first = _cadc_server(name="CANFAR", uri=AnyUrl("ivo://cadc.nrc.ca/skaha"))
        second = _cadc_server(
            name="CANFAR",
            uri=AnyUrl("ivo://canfar.net/src/skaha"),
            url=AnyHttpUrl("https://canfar.net/skaha"),
        )
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.server = [first, second]
            config.save()
            previous = str(Configuration().active.server)

            with (
                patch("canfar.server.Configuration", Configuration),
                pytest.raises(ServerSelectorError, match="Ambiguous") as exc_info,
            ):
                use("CANFAR")

            assert "URI" in (exc_info.value.hint or "")
            assert str(Configuration().active.server) == previous

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
            config.server = [known]
            config.save()

            def merge_discovered(
                config_obj: Configuration,
                _idp: str,
                **_kwargs: object,
            ) -> None:
                config_obj._upsert_server(discovered)  # noqa: SLF001

            with (
                patch(
                    "canfar.server._discover_and_merge",
                    side_effect=merge_discovered,
                ),
                patch("canfar.server._validate_server", return_value=fetched),
                patch("canfar.server.Configuration", Configuration),
            ):
                use("ivo://canfar.cam.uksrc.org/skaha")

            saved = Configuration()
            assert str(saved.active.server) == "ivo://canfar.cam.uksrc.org/skaha"

    def test_use_discovery_failure_leaves_active_unchanged(
        self,
        tmp_path: Path,
    ) -> None:
        """Discovery failure does not change the active server."""
        target = _cadc_server()
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.server = [target]
            config.save()
            previous = str(Configuration().active.server)

            with (
                patch("canfar.server._resolve_selector", return_value=None),
                patch(
                    "canfar.server._discover_and_merge",
                    side_effect=ServerDiscoveryError("registry down"),
                ),
                patch("canfar.server.Configuration", Configuration),
                pytest.raises(ServerDiscoveryError),
            ):
                use("missing-server")

            assert str(Configuration().active.server) == previous

    def test_use_fetch_failure_leaves_active_unchanged(self, tmp_path: Path) -> None:
        """Fetch or validation failure leaves the previous active server."""
        target = _cadc_server()
        config_path = tmp_path / "config.yaml"
        with patch("canfar.models.config.CONFIG_PATH", config_path):
            config = Configuration()
            config.server = [target]
            config.save()
            previous = str(Configuration().active.server)

            with (
                patch(
                    "canfar.server._validate_server",
                    side_effect=ServerFetchError("context unavailable"),
                ),
                patch("canfar.server.Configuration", Configuration),
                pytest.raises(ServerFetchError),
            ):
                use(_CADC_URI)

            assert str(Configuration().active.server) == previous


class TestServerFetch:
    """Tests for Server.fetch() and Server.afetch()."""

    def test_fetch_returns_new_model_without_mutating_original(self) -> None:
        """fetch() returns a populated copy and leaves the source unchanged."""
        server = _cadc_server()
        response = MagicMock()
        response.json.return_value = _CONTEXT_PAYLOAD
        response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.client.get.return_value = response

        with patch("canfar.client.HTTPClient", return_value=mock_client):
            populated = server.fetch()

        assert populated is not server
        assert server.cores == 2
        assert server.ram == 16
        assert server.gpus == 0
        assert populated.cores == 16
        assert populated.ram == 192
        assert populated.gpus == 4

    @pytest.mark.asyncio
    async def test_afetch_returns_new_model_without_mutating_original(self) -> None:
        """afetch() returns a populated copy and leaves the source unchanged."""
        server = _cadc_server()
        response = MagicMock()
        response.json.return_value = _CONTEXT_PAYLOAD
        response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.asynclient.get = AsyncMock(return_value=response)

        with patch("canfar.client.HTTPClient", return_value=mock_client):
            populated = await server.afetch()

        assert populated is not server
        assert populated.cores == 16
        assert populated.ram == 192
        assert populated.gpus == 4

    @pytest.mark.asyncio
    async def test_fetch_and_afetch_return_equivalent_models(self) -> None:
        """Sync and async fetch variants produce equivalent validated state."""
        server = _cadc_server()
        response = MagicMock()
        response.json.return_value = _CONTEXT_PAYLOAD
        response.raise_for_status = MagicMock()

        sync_client = MagicMock()
        sync_client.client.get.return_value = response
        async_client = MagicMock()
        async_client.asynclient.get = AsyncMock(return_value=response)

        with patch("canfar.client.HTTPClient", side_effect=[sync_client, async_client]):
            sync_result = server.fetch()
            async_result = await server.afetch()

        assert sync_result.model_dump() == async_result.model_dump()

    def test_fetch_applies_defaults_when_context_unavailable(self) -> None:
        """fetch() returns default resource settings when context fetch fails."""
        server = _cadc_server()
        mock_client = MagicMock()
        mock_client.client.get.side_effect = OSError("connection refused")

        with patch("canfar.client.HTTPClient", return_value=mock_client):
            populated = server.fetch()

        assert populated is not server
        assert populated.cores == 2
        assert populated.ram == 16
        assert populated.gpus == 0

    @pytest.mark.asyncio
    async def test_afetch_applies_defaults_when_context_unavailable(self) -> None:
        """afetch() returns default resource settings when context fetch fails."""
        server = _cadc_server()
        mock_client = MagicMock()
        mock_client.asynclient.get = AsyncMock(
            side_effect=OSError("connection refused"),
        )

        with patch("canfar.client.HTTPClient", return_value=mock_client):
            populated = await server.afetch()

        assert populated is not server
        assert populated.cores == 2
        assert populated.ram == 16
        assert populated.gpus == 0

    def test_fetch_requires_url_and_version(self) -> None:
        """fetch() rejects servers missing URL or API version."""
        server = _cadc_server(version=None)

        with pytest.raises(ValueError, match="URL and version"):
            server.fetch()


class TestServerDiscovery:
    """Tests for IDP-scoped discovery helpers."""

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
        mock_discovery.extract.return_value = [endpoint]
        mock_discovery.check = AsyncMock(side_effect=lambda item: item)
        mock_discovery.__aenter__ = AsyncMock(return_value=mock_discovery)
        mock_discovery.__aexit__ = AsyncMock(return_value=None)

        with (
            patch("canfar.server.Discover", return_value=mock_discovery),
            patch(
                "canfar.server._enrich_from_capabilities",
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

        with patch(
            "canfar.models.http.vosi.capabilities",
            side_effect=ValueError("mismatched tag"),
        ):
            server = _discovered_to_server(endpoint, "srcnet")

        assert server.idp == "srcnet"
        assert server.name == "Broken"
        assert str(server.url) == "https://broken.example.org/skaha"
        assert server.version is None

    def test_enrich_from_capabilities_non_strict_returns_server_on_failure(
        self,
    ) -> None:
        """Non-strict enrichment preserves registry metadata for listing."""
        server = _cadc_server(version=None, auths=None)

        with patch(
            "canfar.models.http.vosi.capabilities",
            side_effect=ValueError("mismatched tag"),
        ):
            enriched = _enrich_from_capabilities(server, strict=False)

        assert enriched.version is None
        assert enriched.auths is None

    def test_enrich_from_capabilities_strict_raises_on_failure(self) -> None:
        """Strict enrichment fails when capabilities cannot be parsed."""
        server = _cadc_server(version=None, auths=None)

        with (
            patch(
                "canfar.models.http.vosi.capabilities",
                side_effect=ValueError("mismatched tag"),
            ),
            pytest.raises(ServerFetchError, match="Failed to fetch capabilities"),
        ):
            _enrich_from_capabilities(server, strict=True)

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
        mock_discovery.extract.return_value = []
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

    def test_validate_server_honors_timeout(self) -> None:
        """Server validation passes login timeout to capabilities and fetch."""
        server = _cadc_server(version=None, auths=None)
        fetched = server.model_copy(
            update={"version": "v1", "auths": ["x509"], "cores": 16},
            deep=True,
        )

        with (
            patch.object(
                Server,
                "capabilities",
                return_value=[
                    {
                        "baseurl": _CADC_URL,
                        "version": "v1",
                        "auth_modes": ["x509"],
                    }
                ],
            ) as capabilities,
            patch.object(Server, "fetch", return_value=fetched) as fetch,
        ):
            validated = _validate_server(server, timeout=13)

        assert validated.cores == 16
        capabilities.assert_called_once_with(timeout=13)
        fetch.assert_called_once_with(timeout=13)


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
