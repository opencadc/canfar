"""Comprehensive tests for the registry models module."""

import base64

import pytest
from pydantic import AnyHttpUrl, ValidationError

from canfar.models.registry import (
    ContainerRegistry,
    IVOARegistry,
    RegistryCredential,
    Server,
)
from canfar.utils import discover


class TestDiscoveryConstants:
    """Discovery skips and names records from fixed module constants."""

    def test_constants(self) -> None:
        """Known omissions, development markers, and Server Names are fixed."""
        assert ("CADC", "ivo://canfar.net/src/skaha") in discover.OMIT
        assert {"dev", "test", "staging"} <= set(discover.DEVELOPMENT_MARKERS)
        assert discover.NAMES["ivo://cadc.nrc.ca/skaha"] == "canfar"


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


class TestContainerRegistry:
    """Runtime and saved Container Registry credentials."""

    def test_defaults_to_canfar_host(self) -> None:
        """A runtime credential without a URL applies to images.canfar.net."""
        registry = ContainerRegistry(username="testuser", secret="testsecret")
        assert registry.url == "images.canfar.net"
        assert registry.secret.get_secret_value() == "testsecret"
        assert "testsecret" not in repr(registry)

    @pytest.mark.parametrize(
        ("url", "host"),
        [
            ("https://Registry.Example.com/", "registry.example.com"),
            ("http://localhost:5000", "localhost:5000"),
            ("harbor.local:5000", "harbor.local:5000"),
            (AnyHttpUrl("https://images.canfar.net"), "images.canfar.net"),
        ],
    )
    def test_url_is_reduced_to_host(self, url, host) -> None:
        """Bare hosts and http(s) URLs normalize to the same registry host."""
        registry = ContainerRegistry(url=url, username="user", secret="secret")
        assert registry.url == host

    @pytest.mark.parametrize(
        "url",
        ["sftp://registry.com", "https://registry.com/project", "https://", ""],
    )
    def test_url_rejects_non_hosts(self, url) -> None:
        """Other schemes, paths, and empty hosts are not registry hosts."""
        with pytest.raises(ValidationError, match="container registry host"):
            ContainerRegistry(url=url, username="user", secret="secret")

    @pytest.mark.parametrize(
        "kwargs",
        [{"username": "user"}, {"secret": "secret"}],
        ids=["no-secret", "no-username"],
    )
    def test_credential_needs_username_and_secret(self, kwargs) -> None:
        """A username without a secret, or the reverse, is invalid."""
        with pytest.raises(ValidationError):
            ContainerRegistry(**kwargs)

    @pytest.mark.parametrize(
        ("username", "secret"),
        [("testuser", "testsecret"), ("user@domain.com", "p@ssw0rd!")],
    )
    def test_header_is_base64_username_secret(self, username, secret) -> None:
        """The header value is base64 of ``username:secret``."""
        registry = ContainerRegistry(username=username, secret=secret)
        expected = base64.b64encode(f"{username}:{secret}".encode()).decode()
        assert registry.credential.header() == expected
        assert RegistryCredential(username=username, secret=secret).header() == (
            expected
        )

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
        """Usernames and secrets are 1 to 255 characters."""
        kwargs = {"username": "user", "secret": "secret"}
        kwargs[field] = value
        if is_valid:
            RegistryCredential(**kwargs)
        else:
            with pytest.raises(ValidationError):
                RegistryCredential(**kwargs)
