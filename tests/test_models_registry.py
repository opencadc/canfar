"""Comprehensive tests for the registry models module."""

import base64
import math

import pytest
from pydantic import ValidationError

from canfar.models.registry import (
    ContainerRegistry,
    IVOARegistry,
    IVOARegistrySearch,
    Server,
    ServerResults,
)


class TestIVOARegistrySearch:
    """Test IVOARegistrySearch class."""

    def test_default_values(self) -> None:
        """Test default values for IVOARegistrySearch."""
        search = IVOARegistrySearch()

        expected_names = {
            "ivo://canfar.net/src/skaha": "Canada",
            "ivo://swesrc.chalmers.se/skaha": "Sweden",
            "ivo://canfar.cam.uksrc.org/skaha": "UK-CAM",
            "ivo://canfar.ral.uksrc.org/skaha": "UK-RAL",
            "ivo://src.skach.org/skaha": "Swiss",
            "ivo://espsrc.iaa.csic.es/skaha": "Spain",
            "ivo://canfar.itsrc.oact.inaf.it/skaha": "Italy",
            "ivo://shion-sp.mtk.nao.ac.jp/skaha": "Japan",
            "ivo://canfar.krsrc.kr/skaha": "Korea",
            "ivo://canfar.ska.zverse.space/skaha": "China",
            "ivo://cadc.nrc.ca/skaha": "CANFAR",
        }
        assert search.names == expected_names

        assert ("CADC", "ivo://canfar.net/src/skaha") in search.omit
        assert "dev" in search.excluded
        assert "test" in search.excluded
        assert "staging" in search.excluded

    def test_with_custom_values(self) -> None:
        """Test IVOARegistrySearch with custom values."""
        custom_registries = {"https://custom.registry.com": "Custom"}
        custom_names = {"ivo://custom.com/service": "Custom Service"}
        custom_omit = [("Custom", "ivo://custom.com/service")]
        custom_excluded = ("custom", "exclude")

        search = IVOARegistrySearch(
            registries=custom_registries,
            names=custom_names,
            omit=custom_omit,
            excluded=custom_excluded,
        )

        assert search.registries == custom_registries
        assert search.names == custom_names
        assert search.omit == custom_omit
        assert search.excluded == custom_excluded


class TestIVOARegistry:
    """Test IVOARegistry class."""

    def test_default_values(self) -> None:
        """Test default values for IVOARegistry."""
        registry = IVOARegistry(name="Test Registry", content="<xml>content</xml>")

        assert registry.name == "Test Registry"
        assert registry.content == "<xml>content</xml>"
        assert registry.success is True
        assert registry.error is None

    def test_with_error(self) -> None:
        """Test IVOARegistry with error."""
        registry = IVOARegistry(
            name="Failed Registry",
            content="",
            success=False,
            error="Connection failed",
        )

        assert registry.name == "Failed Registry"
        assert registry.content == ""
        assert registry.success is False
        assert registry.error == "Connection failed"

    def test_required_fields(self) -> None:
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            IVOARegistry(content="content")

        with pytest.raises(ValidationError):
            IVOARegistry(name="name")


class TestServer:
    """Test Server class."""

    @pytest.mark.parametrize(
        ("server_data", "expected_status", "expected_name"),
        [
            (
                {
                    "registry": "CADC",
                    "uri": "ivo://cadc.nrc.ca/skaha",
                    "url": "https://ws-uv.canfar.net/skaha",
                },
                None,
                None,
            ),
            (
                {
                    "registry": "SRCnet",
                    "uri": "ivo://swesrc.chalmers.se/skaha",
                    "url": "https://services.swesrc.chalmers.se/skaha",
                    "status": 200,
                    "name": "Sweden",
                },
                200,
                "Sweden",
            ),
        ],
    )
    def test_server_creation(self, server_data, expected_status, expected_name) -> None:
        """Test Server creation with and without optional fields."""
        server = Server(**server_data)
        for key, value in server_data.items():
            assert getattr(server, key) == value
        assert server.status == expected_status
        assert server.name == expected_name

    @pytest.mark.parametrize(
        "server_data",
        [
            {"uri": "ivo://test.com", "url": "https://test.com"},
            {"registry": "Test", "url": "https://test.com"},
            {"registry": "Test", "uri": "ivo://test.com"},
        ],
    )
    def test_missing_required_fields(self, server_data) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Server(**server_data)


class TestServerResults:
    """Test ServerResults class."""

    def test_default_values(self) -> None:
        """Test default values for ServerResults."""
        results = ServerResults()

        assert results.endpoints == []
        assert math.isclose(results.total_time, 0.0, abs_tol=1e-9)
        assert math.isclose(results.registry_fetch_time, 0.0, abs_tol=1e-9)
        assert math.isclose(results.endpoint_check_time, 0.0, abs_tol=1e-9)
        assert results.found == 0
        assert results.checked == 0
        assert results.successful == 0

    def test_with_custom_values(self) -> None:
        """Test ServerResults with custom values."""
        endpoints = [
            Server(
                registry="CADC",
                uri="ivo://cadc.nrc.ca/skaha",
                url="https://ws-uv.canfar.net/skaha",
            )
        ]

        results = ServerResults(
            endpoints=endpoints,
            total_time=5.5,
            registry_fetch_time=2.0,
            endpoint_check_time=3.5,
            found=10,
            checked=8,
            successful=6,
        )

        assert len(results.endpoints) == 1
        assert math.isclose(results.total_time, 5.5, rel_tol=1e-9, abs_tol=1e-9)
        assert math.isclose(
            results.registry_fetch_time, 2.0, rel_tol=1e-9, abs_tol=1e-9
        )
        assert math.isclose(
            results.endpoint_check_time, 3.5, rel_tol=1e-9, abs_tol=1e-9
        )
        assert results.found == 10
        assert results.checked == 8
        assert results.successful == 6

    def test_add_method(self) -> None:
        """Test add method."""
        results = ServerResults()

        successful_server = Server(
            registry="CADC",
            uri="ivo://cadc.nrc.ca/skaha",
            url="https://ws-uv.canfar.net/skaha",
            status=200,
        )
        results.add(successful_server)

        assert len(results.endpoints) == 1
        assert results.successful == 1

        failed_server = Server(
            registry="Failed",
            uri="ivo://failed.com/skaha",
            url="https://failed.com/skaha",
            status=500,
        )
        results.add(failed_server)

        assert len(results.endpoints) == 2
        assert results.successful == 1

    def test_get_by_registry_method(self) -> None:
        """Test get_by_registry method."""
        results = ServerResults()

        cadc_server1 = Server(
            registry="CADC", uri="ivo://cadc1.com", url="https://cadc1.com"
        )
        cadc_server2 = Server(
            registry="CADC", uri="ivo://cadc2.com", url="https://cadc2.com"
        )
        srcnet_server = Server(
            registry="SRCnet", uri="ivo://srcnet.com", url="https://srcnet.com"
        )

        results.add(cadc_server1)
        results.add(cadc_server2)
        results.add(srcnet_server)

        grouped = results.get_by_registry()

        assert "CADC" in grouped
        assert "SRCnet" in grouped
        assert len(grouped["CADC"]) == 2
        assert len(grouped["SRCnet"]) == 1
        assert grouped["CADC"][0] == cadc_server1
        assert grouped["CADC"][1] == cadc_server2
        assert grouped["SRCnet"][0] == srcnet_server


class TestContainerRegistry:
    """Test ContainerRegistry class."""

    def test_default_values(self) -> None:
        """Test default values for ContainerRegistry."""
        registry = ContainerRegistry()
        assert registry.url is None
        assert registry.username is None
        assert registry.secret is None

    def test_with_all_values(self) -> None:
        """Test ContainerRegistry with all values."""
        registry = ContainerRegistry(
            url="https://registry.example.com",
            username="testuser",
            secret="testsecret",
        )
        assert str(registry.url) == "https://registry.example.com/"
        assert registry.username == "testuser"
        assert registry.secret == "testsecret"

    @pytest.mark.parametrize(
        ("username", "secret", "message"),
        [
            ("user", None, "container registry secret is required"),
            (None, "secret", "container registry username is required"),
        ],
    )
    def test_credentials_validation(self, username, secret, message) -> None:
        """Test validation for credential pairs."""
        with pytest.raises(ValidationError, match=message):
            ContainerRegistry(username=username, secret=secret)

    @pytest.mark.parametrize(
        ("username", "secret"),
        [("testuser", "testsecret"), ("user@domain.com", "p@ssw0rd!")],
    )
    def test_encoded(self, username, secret) -> None:
        """Test encoded method."""
        registry = ContainerRegistry(username=username, secret=secret)
        expected = base64.b64encode(f"{username}:{secret}".encode()).decode()
        assert registry.encoded() == expected

    @pytest.mark.parametrize(
        ("url", "is_valid"),
        [
            ("https://registry.example.com", True),
            ("http://localhost:5000", True),
            ("not-a-valid-url", False),
            ("sftp://registry.com", False),
        ],
    )
    def test_url_validation(self, url, is_valid) -> None:
        """Test URL field validation."""
        if is_valid:
            registry = ContainerRegistry(url=url)
            assert str(registry.url).startswith(url)
        else:
            with pytest.raises(ValidationError):
                ContainerRegistry(url=url)

    @pytest.mark.parametrize(
        ("field", "value", "is_valid"),
        [
            ("username", "a", True),
            ("username", "a" * 255, True),
            ("username", "", False),
            ("username", "a" * 256, False),
            ("secret", "s", True),
            ("secret", "s" * 255, True),
            ("secret", "", False),
            ("secret", "s" * 256, False),
        ],
    )
    def test_field_length_validation(self, field, value, is_valid) -> None:
        """Test field length validation."""
        kwargs = {"username": "user", "secret": "secret"}
        kwargs[field] = value
        if is_valid:
            registry = ContainerRegistry(**kwargs)
            assert getattr(registry, field) == value
        else:
            with pytest.raises(ValidationError):
                ContainerRegistry(**kwargs)
