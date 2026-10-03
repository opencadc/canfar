"""Comprehensive tests for the HTTP models module."""

import pytest
from pydantic import ValidationError

from canfar.models.http import (
    ResourceRange,
    Server,
    ServerResources,
    SessionResources,
    VOSpaceService,
)

_LIMIT_RANGE_CONTEXT = {
    "cores": {
        "default": 1,
        "defaultRequest": 1,
        "defaultLimit": 2,
        "options": list(range(1, 35)),
    },
    "memoryGB": {
        "default": 2,
        "defaultRequest": 2,
        "defaultLimit": 4,
        "options": list(range(1, 385)),
    },
    "gpus": {"options": []},
    "maxInteractiveSessions": 5,
}
"""Context payload from a Server that derives limits from a LimitRange."""


class TestVOSpaceService:
    """Test VOSpace Service configuration."""

    def test_serializes_registry_uri_and_http_endpoint(self) -> None:
        """A VOSpace Service carries only its registry URI and base URL."""
        service = VOSpaceService(
            uri="ivo://cadc.nrc.ca/arc",
            url="https://ws-cadc.canfar.net/arc",
        )

        assert service.model_dump(mode="json") == {
            "uri": "ivo://cadc.nrc.ca/arc",
            "url": "https://ws-cadc.canfar.net/arc",
        }

    @pytest.mark.parametrize(
        "payload",
        [
            {"uri": "not-a-url", "url": "https://ws-cadc.canfar.net/arc"},
            {"uri": "ivo://cadc.nrc.ca/arc", "url": "vos://example.com/arc"},
            {"url": "https://ws-cadc.canfar.net/arc"},
            {"uri": "ivo://cadc.nrc.ca/arc"},
        ],
    )
    def test_requires_valid_registry_uri_and_http_endpoint(self, payload: dict) -> None:
        """Both VOSpace Service identifiers are required and validated."""
        with pytest.raises(ValidationError):
            VOSpaceService.model_validate(payload)

    @pytest.mark.parametrize(
        "url",
        [
            "https://ws-cadc.canfar.net/arc/capabilities",
            "https://ws-cadc.canfar.net/arc/capabilities/",
        ],
    )
    def test_rejects_capabilities_endpoint_as_base_url(self, url: str) -> None:
        """A VOSpace Service URL names the base service, not capabilities."""
        with pytest.raises(ValidationError, match="must not end with /capabilities"):
            VOSpaceService(uri="ivo://cadc.nrc.ca/arc", url=url)


class TestServer:
    """Test Server class."""

    def test_model_ignores_environment_and_has_no_network_methods(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Persisted Server data comes only from validated input."""
        monkeypatch.setenv("CANFAR_SERVER_NAME", "Environment Server")
        monkeypatch.setenv("CANFAR_SERVER_RESOURCES", '{"sessions": 64}')

        server = Server()

        assert server.name is None
        assert server.resources is None
        assert not hasattr(server, "capabilities")
        assert not hasattr(server, "fetch")
        assert not hasattr(server, "afetch")

    def test_default_values(self) -> None:
        """Test default values for Server."""
        server = Server()
        assert server.name is None
        assert server.uri is None
        assert server.url is None
        assert server.version is None
        assert server.storage == {}

    def test_with_all_values(self) -> None:
        """Test Server with all custom values."""
        server = Server(
            name="Test Server",
            uri="ivo://test.example.com/skaha",
            url="https://test.example.com/skaha",
            version="v1",
        )

        assert server.name == "Test Server"
        assert str(server.uri) == "ivo://test.example.com/skaha"
        assert str(server.url) == "https://test.example.com/skaha"
        assert server.version == "v1"

    def test_with_partial_values(self) -> None:
        """Test Server with partial values."""
        server = Server(name="Partial Server", url="https://example.com")

        assert server.name == "Partial Server"
        assert server.uri is None
        assert str(server.url) == "https://example.com/"  # pydantic adds trailing slash
        assert server.version is None

    def test_name_validation(self) -> None:
        """Test name field validation."""
        # Valid names
        server = Server(name="Valid Name")
        assert server.name == "Valid Name"

        server = Server(name="A" * 256)  # Max length
        assert len(server.name) == 256

        # Invalid names
        with pytest.raises(ValidationError):
            Server(name="")  # Empty string

        with pytest.raises(ValidationError):
            Server(name="A" * 257)  # Too long

    def test_uri_validation(self) -> None:
        """Test URI field validation."""
        # Valid URIs
        server = Server(uri="ivo://example.com/service")
        assert str(server.uri) == "ivo://example.com/service"

        server = Server(uri="https://example.com/path")
        assert str(server.uri) == "https://example.com/path"

        # Invalid URIs
        with pytest.raises(ValidationError):
            Server(uri="not-a-valid-uri")

        with pytest.raises(ValidationError):
            Server(uri="")

    def test_url_validation(self) -> None:
        """Test URL field validation."""
        # Valid URLs
        server = Server(url="https://example.com")
        assert str(server.url) == "https://example.com/"  # pydantic adds trailing slash

        server = Server(url="http://localhost:8080/path")
        assert str(server.url) == "http://localhost:8080/path"

        # Invalid URLs
        with pytest.raises(ValidationError):
            Server(url="not-a-valid-url")

        with pytest.raises(ValidationError):
            Server(url="sftp://example.com")  # Not HTTP/HTTPS

    def test_version_validation(self) -> None:
        """Test version field validation."""
        # Valid versions
        server = Server(version="v0")
        assert server.version == "v0"

        server = Server(version="v123")
        assert server.version == "v123"

        server = Server(version="v2.1")
        assert server.version == "v2.1"

        server = Server(version="v9999999")  # Max length test
        assert server.version == "v9999999"

        # Invalid versions
        with pytest.raises(ValidationError):
            Server(version="1")  # Missing 'v' prefix

        with pytest.raises(ValidationError):
            Server(version="version1")  # Wrong format

        with pytest.raises(ValidationError):
            Server(version="v")  # Too short

        with pytest.raises(ValidationError):
            Server(version="v" + "1" * 8)  # Too long

    def test_model_config_settings(self) -> None:
        """Test model configuration settings."""
        # Test that extra fields are forbidden
        with pytest.raises(ValidationError):
            Server(invalid_field="value")

        # Test string stripping
        server = Server(name="  Trimmed Name  ")
        assert server.name == "Trimmed Name"

    def test_examples_from_field_definitions(self) -> None:
        """Test that examples from field definitions work."""
        # Test examples from name field
        server = Server(name="SRCnet-Sweden")
        assert server.name == "SRCnet-Sweden"

        server = Server(name="SRCnet-UK-CAM")
        assert server.name == "SRCnet-UK-CAM"

        # Test examples from URI field
        server = Server(uri="ivo://swesrc.chalmers.se/skaha")
        assert str(server.uri) == "ivo://swesrc.chalmers.se/skaha"

        # Test examples from URL field
        server = Server(url="https://services.swesrc.chalmers.se/skaha")
        assert str(server.url) == "https://services.swesrc.chalmers.se/skaha"


class TestServerResources:
    """Test Session resource limits read from context payloads."""

    def test_reads_flexible_and_fixed_limits_from_context(self) -> None:
        """Flexible spans request to limit; fixed spans the offered options."""
        resources = ServerResources.from_context(_LIMIT_RANGE_CONTEXT)

        assert resources.model_dump() == {
            "flexible": {"cores": {"min": 1, "max": 2}, "ram": {"min": 2, "max": 4}},
            "fixed": {"cores": {"min": 1, "max": 34}, "ram": {"min": 1, "max": 384}},
            "gpus": {"min": 0, "max": 0},
            "sessions": 5,
        }

    def test_reads_file_based_context_with_sparse_options(self) -> None:
        """File-based contexts may send sparse options and a quoted Session count."""
        resources = ServerResources.from_context(
            {
                "cores": {
                    "defaultRequest": 1,
                    "defaultLimit": 8,
                    "options": [16, 1, 2],
                },
                "memoryGB": {
                    "defaultRequest": 4,
                    "defaultLimit": 32,
                    "options": [1, 2, 4, 192],
                },
                "gpus": {"options": [1, 2, 28]},
                "maxInteractiveSessions": "5",
            }
        )

        assert resources.fixed == SessionResources(
            cores=ResourceRange(min=1, max=16),
            ram=ResourceRange(min=1, max=192),
        )
        assert resources.gpus == ResourceRange(min=1, max=28)
        assert resources.sessions == 5

    def test_missing_or_malformed_values_stay_unknown(self) -> None:
        """Older platforms produce partial resources instead of invented defaults."""
        resources = ServerResources.from_context(
            {
                "cores": {"defaultRequest": 8, "defaultLimit": 2, "options": [1, 2]},
                "memoryGB": {"defaultRequest": 2, "defaultLimit": 20, "options": []},
                "maxInteractiveSessions": 0,
            }
        )

        assert resources == ServerResources(
            flexible=SessionResources(ram=ResourceRange(min=2, max=20)),
            fixed=SessionResources(cores=ResourceRange(min=1, max=2)),
        )

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"error": "not found"},
            {
                "cores": {"default-request": 1, "default-limit": 16},
                "memory": {"options-gb": [1, 2, 4]},
            },
        ],
        ids=["empty", "unrelated", "pre-2024-keys"],
    )
    def test_rejects_payloads_without_recognizable_limits(self, payload: dict) -> None:
        """A payload with no recognizable limit is not usable resources."""
        with pytest.raises(ValueError, match="no recognizable resource limits"):
            ServerResources.from_context(payload)

    @pytest.mark.parametrize(
        "bounds",
        [{"min": 3, "max": 2}, {"min": -1, "max": 2}, {"min": 1}],
    )
    def test_range_rejects_invalid_bounds(self, bounds: dict) -> None:
        """Ranges are inclusive, non-negative, and need both bounds."""
        with pytest.raises(ValidationError):
            ResourceRange.model_validate(bounds)

    def test_server_round_trips_resources_and_omits_unknown_values(self) -> None:
        """Saved configuration omits unknown limits and reloads the same model."""
        server = Server(
            name="canSRC",
            resources=ServerResources(gpus=ResourceRange(min=0, max=0), sessions=5),
        )

        saved = server.model_dump(mode="json", exclude_none=True)

        assert saved["resources"] == {
            "flexible": {},
            "fixed": {},
            "gpus": {"min": 0, "max": 0},
            "sessions": 5,
        }
        assert Server.model_validate(saved) == server
