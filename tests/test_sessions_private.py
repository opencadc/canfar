"""Private-image Session.create sends registry auth only on POST /session."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx2
import pytest
from pydantic import SecretStr

from canfar.exceptions.session import RegistryCredentialsRequired
from canfar.models.config import Configuration
from canfar.models.registry import RegistryCredential
from canfar.models.session import CreateRequest
from canfar.sessions import AsyncSession, Session

if TYPE_CHECKING:
    from pathlib import Path

_BASE_URL = "https://example.test/skaha/v1/"
_IMAGE = "images.canfar.net/lisa-ddpc/protolab:latest"
_HEADER = "X-Skaha-Registry-Auth"
_AUTH = base64.b64encode(b"ada:harbor-s3cret").decode()


@pytest.fixture
def config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Configuration:
    """Configuration with one saved credential for images.canfar.net."""
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml")
    return Configuration(
        registries={
            "images.canfar.net": RegistryCredential(
                username="ada", secret=SecretStr("harbor-s3cret")
            )
        }
    )


def _recorder(seen: list[httpx2.Request]):
    def respond(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        if request.method == "POST":
            name = request.url.params["name"]
            return httpx2.Response(200, text=f"{name}-id\n", request=request)
        return httpx2.Response(200, json=[], request=request)

    return respond


def _sync_session(seen: list[httpx2.Request], config: Configuration):
    real_client = httpx2.Client
    return patch(
        "canfar.client.Client",
        side_effect=lambda **kwargs: real_client(
            transport=httpx2.MockTransport(_recorder(seen)), **kwargs
        ),
    ), Session(token=SecretStr("token"), url=_BASE_URL, config=config)


@pytest.mark.parametrize("private", [True, False])
def test_sync_create_sends_registry_auth_only_on_private_posts(
    config: Configuration, private: bool
) -> None:
    """Each replica POST carries the header when private; no other request does."""
    seen: list[httpx2.Request] = []
    transport, session = _sync_session(seen, config)
    with transport, session:
        ids = session.create(
            "proto", _IMAGE, kind="headless", replicas=3, private=private
        )
        session.fetch()

    assert ids == ["proto-1-id", "proto-2-id", "proto-3-id"]
    posts = [request for request in seen if request.method == "POST"]
    expected = _AUTH if private else None
    assert [request.headers.get(_HEADER) for request in posts] == [expected] * 3
    assert [request.method for request in seen if _HEADER in request.headers] == (
        ["POST"] * 3 if private else []
    )
    assert all("private" not in request.url.params for request in posts)


@pytest.mark.asyncio
async def test_async_create_sends_registry_auth_from_a_private_request(
    config: Configuration,
) -> None:
    """``CreateRequest.private`` sends the header on every async replica POST."""
    seen: list[httpx2.Request] = []
    real_async_client = httpx2.AsyncClient
    request = CreateRequest(
        name="proto", image=_IMAGE, kind="headless", replicas=2, private=True
    )
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx2.MockTransport(_recorder(seen)), **kwargs
        ),
    ):
        async with AsyncSession(
            token=SecretStr("token"), url=_BASE_URL, config=config
        ) as session:
            assert await session.create(request) == ["proto-1-id", "proto-2-id"]
            await session.fetch()

    assert [(r.method, r.headers.get(_HEADER)) for r in seen] == [
        ("POST", _AUTH),
        ("POST", _AUTH),
        ("GET", None),
    ]


@pytest.mark.asyncio
async def test_private_create_without_credential_sends_no_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing credential raises before the first POST, sync and async."""
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", tmp_path / "config.yaml")
    config = Configuration(
        registries={
            "harbor.example": RegistryCredential(
                username="ada", secret=SecretStr("other")
            )
        }
    )
    seen: list[httpx2.Request] = []
    transport, session = _sync_session(seen, config)
    with (
        transport,
        session,
        pytest.raises(RegistryCredentialsRequired) as raised,
    ):
        session.create("proto", _IMAGE, private=True)
    assert raised.value.host == "images.canfar.net"

    real_async_client = httpx2.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx2.MockTransport(_recorder(seen)), **kwargs
        ),
    ):
        async with AsyncSession(
            token=SecretStr("token"), url=_BASE_URL, config=config
        ) as async_session:
            with pytest.raises(RegistryCredentialsRequired):
                await async_session.create("proto", _IMAGE, replicas=2, private=True)

    assert seen == []


def test_private_flag_with_a_request_is_a_type_error(config: Configuration) -> None:
    """``private=True`` beside a ``CreateRequest`` is rejected, not ignored."""
    seen: list[httpx2.Request] = []
    transport, session = _sync_session(seen, config)
    request = CreateRequest(name="proto", image=_IMAGE, kind="headless")
    with transport, session, pytest.raises(TypeError, match="CreateRequest"):
        session.create(request, private=True)
    assert seen == []
