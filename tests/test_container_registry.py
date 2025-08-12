"""Test ContainerRegistry model."""

import pytest
from pydantic import ValidationError

from canfar.models.registry import ContainerRegistry


def test_valid_container_registry() -> None:
    """Test valid container registry."""
    valid = {
        "url": "https://images.canfar.net",
        "username": "test",
        "secret": "ghp_1234567890",
    }
    registry = ContainerRegistry(**valid)
    assert str(registry.url) == "https://images.canfar.net/"
    assert registry.username == "test"  # nosec
    assert registry.secret == "ghp_1234567890"  # nosec


def test_invalid_container_registry_missing_username() -> None:
    """Test invalid container registry missing username."""
    invalid_data = {"url": "images.canfar.net", "secret": "ghp_1234567890"}  # nosec
    with pytest.raises(ValidationError):
        ContainerRegistry(**invalid_data)


def test_invalid_container_registry_missing_secret() -> None:
    """Test invalid container registry missing secret."""
    invalid_data = {"server": "images.canfar.net", "username": "test"}  # nosec
    with pytest.raises(ValidationError):
        ContainerRegistry(**invalid_data)


def test_invalid_container_registry_wrong_server() -> None:
    """Test invalid container registry wrong server."""
    invalid_data = {
        "url": "invalid.server.net",
        "username": "test",
        "secret": "ghp_1234567890",
    }
    with pytest.raises(ValidationError):
        ContainerRegistry(**invalid_data)


def test_base64_encoding() -> None:
    """Test base64 encoding."""
    registry = ContainerRegistry(username="test", secret="supersecret")  # nosec
    # Encoding basedon https://www.base64encode.org/
    assert registry.encoded() == "dGVzdDpzdXBlcnNlY3JldA=="  # nosec
