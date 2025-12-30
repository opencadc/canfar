"""Test Canfar Images API."""

from unittest.mock import patch

import pytest

from canfar.images import Images
from canfar.models.containers import Image


@pytest.fixture(scope="session")
def images():
    """Test images."""
    images = Images()
    yield images
    del images


def test_images_fetch(images: Images) -> None:
    """Test fetching images."""
    assert len(images.fetch()) > 0


def test_images_with_kind(images: Images) -> None:
    """Test fetching images with kind."""
    assert "images.canfar.net/skaha/base-notebook:latest" in images.fetch(
        kind="notebook",
    )


def test_images_details_returns_models() -> None:
    """Ensure details returns Image models."""
    payload = [
        {
            "id": "images.canfar.net/skaha/terminal:1.1.1",
            "types": ["headless", "notebook"],
            "digest": "sha256:deadbeef",
        }
    ]
    images = Images()

    with patch("canfar.images.HTTPClient.client") as client:
        client.get.return_value.json.return_value = payload
        results = images.details()

    assert isinstance(results[0], Image)
    assert results[0].id == payload[0]["id"]
    assert results[0].types == payload[0]["types"]
    assert results[0].digest == payload[0]["digest"]
