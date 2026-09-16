"""Paired public contracts for synchronous and asynchronous Session reads."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from canfar.sessions import AsyncSession, Session

_FETCH_PAYLOAD = [{"id": "session-1", "name": "notebook", "status": "Running"}]
_FETCH_FILTERS = {"kind": "notebook", "status": "Running", "view": "all"}
_FETCH_PARAMS = [("type", "notebook"), ("status", "Running"), ("view", "all")]
_STATS_PAYLOAD = {"cores": {"available": 4}, "ram": {"available": "8G"}}
_BASE_URL = "https://example.test/skaha/v1/"


def test_sync_fetch_preserves_request_and_response_contract() -> None:
    """Sync fetch preserves filters and the server response shape."""
    sent: list[tuple[str, str]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        sent.extend(request.url.params.multi_items())
        return httpx.Response(200, json=_FETCH_PAYLOAD, request=request)

    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(respond),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert session.fetch(**_FETCH_FILTERS) == _FETCH_PAYLOAD

    assert sent == _FETCH_PARAMS


@pytest.mark.asyncio
async def test_async_fetch_preserves_request_and_response_contract() -> None:
    """Async fetch preserves filters and the server response shape."""
    sent: list[tuple[str, str]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        sent.extend(request.url.params.multi_items())
        return httpx.Response(200, json=_FETCH_PAYLOAD, request=request)

    real_async_client = httpx.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(respond),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.fetch(**_FETCH_FILTERS) == _FETCH_PAYLOAD

    assert sent == _FETCH_PARAMS


def test_sync_stats_preserves_response_shape() -> None:
    """Sync stats returns the decoded platform response."""
    sent: list[tuple[str, str]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        sent.extend(request.url.params.multi_items())
        return httpx.Response(200, json=_STATS_PAYLOAD, request=request)

    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(respond),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert session.stats() == _STATS_PAYLOAD

    assert sent == [("view", "stats")]


@pytest.mark.asyncio
async def test_async_stats_preserves_response_shape() -> None:
    """Async stats returns the decoded platform response."""
    sent: list[tuple[str, str]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        sent.extend(request.url.params.multi_items())
        return httpx.Response(200, json=_STATS_PAYLOAD, request=request)

    real_async_client = httpx.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(respond),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.stats() == _STATS_PAYLOAD

    assert sent == [("view", "stats")]


@pytest.mark.parametrize("field", ["kind", "status", "view"])
def test_sync_fetch_rejects_invalid_filter(field: str) -> None:
    """Invalid Session filters fail at the synchronous public boundary."""
    with (
        Session(token=SecretStr("token"), url="https://example.test") as session,
        pytest.raises(ValidationError),
    ):
        session.fetch(**{field: "invalid"})


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["kind", "status", "view"])
async def test_async_fetch_rejects_invalid_filter(field: str) -> None:
    """Invalid Session filters fail at the asynchronous public boundary."""
    async with AsyncSession(
        token=SecretStr("token"), url="https://example.test"
    ) as session:
        with pytest.raises(ValidationError):
            await session.fetch(**{field: "invalid"})
