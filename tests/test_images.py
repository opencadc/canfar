"""Test Canfar Images API."""

import httpx
import pytest
from pydantic import SecretStr

from canfar.images import Images
from canfar.models.containers import Image


@pytest.fixture(scope="session")
def images():
    """Test images."""
    images = Images()
    try:
        yield images
    finally:
        images.__exit__(None, None, None)


@pytest.mark.integration
@pytest.mark.slow
def test_images_fetch(images: Images) -> None:
    """Test fetching images."""
    assert len(images.fetch()) > 0


@pytest.mark.integration
@pytest.mark.slow
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

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, request=request)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "canfar.client.Client",
            lambda **kwargs: httpx.Client(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        )
        with Images(token=SecretStr("token"), url="https://example.test") as images:
            results = images.details()

    assert isinstance(results[0], Image)
    assert results[0].id == payload[0]["id"]
    assert results[0].types == payload[0]["types"]
    assert results[0].digest == payload[0]["digest"]


def test_images_fetch_uses_http_client_params() -> None:
    """Fetch returns image IDs and passes optional kind as request parameter."""
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json=[{"id": "images.canfar.net/skaha/terminal:latest"}],
            request=request,
        )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "canfar.client.Client",
            lambda **kwargs: httpx.Client(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        )
        with Images(
            token=SecretStr("token"), url="https://example.test/skaha/v1"
        ) as images:
            assert images.fetch() == ["images.canfar.net/skaha/terminal:latest"]
            assert images.fetch(kind="headless") == [
                "images.canfar.net/skaha/terminal:latest"
            ]

    assert [request.url.params.multi_items() for request in requests] == [
        [],
        [("type", "headless")],
    ]
