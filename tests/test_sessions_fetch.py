"""Paired public contracts for synchronous and asynchronous Session reads."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx2
import pytest
from pydantic import SecretStr, ValidationError

from canfar.sessions import AsyncSession, Session

_FETCH_PAYLOAD = [{"id": "session-1", "name": "notebook", "status": "Running"}]
_FETCH_FILTERS = {"kind": "notebook", "status": "Running"}
_FETCH_PARAMS = [("type", "notebook"), ("status", "Running")]
_STATS_PAYLOAD = {"cores": {"available": 4}, "ram": {"available": "8G"}}
_GPU_STATS_PAYLOAD = {
    "cores": {
        "requestedCPUCores": 873.25,
        "cpuCoresAvailable": 3000.0,
        "maxCPUCores": {"cpuCores": 16.0, "withRam": "192G"},
    },
    "ram": {
        "requestedRAM": "9432.822G",
        "ramAvailable": "15032.386G",
        "maxRAM": {"ram": "192G", "withCPUCores": 16.0},
    },
    "gpu": {"requestedGPU": 15, "gpuAvailable": 112, "maxGPU": 7},
}
_BASE_URL = "https://example.test/skaha/v1/"


def test_sync_fetch_preserves_request_and_response_contract() -> None:
    """Sync fetch preserves filters and the server response shape."""
    sent: list[tuple[str, str]] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        sent.extend(request.url.params.multi_items())
        return httpx2.Response(200, json=_FETCH_PAYLOAD, request=request)

    real_client = httpx2.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx2.MockTransport(respond),
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

    def respond(request: httpx2.Request) -> httpx2.Response:
        sent.extend(request.url.params.multi_items())
        return httpx2.Response(200, json=_FETCH_PAYLOAD, request=request)

    real_async_client = httpx2.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx2.MockTransport(respond),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.fetch(**_FETCH_FILTERS) == _FETCH_PAYLOAD

    assert sent == _FETCH_PARAMS


@pytest.mark.parametrize("payload", [_STATS_PAYLOAD, _GPU_STATS_PAYLOAD])
def test_sync_stats_preserves_response_shape(payload: dict[str, Any]) -> None:
    """Sync stats returns the decoded platform response."""
    sent: list[tuple[str, str]] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        sent.extend(request.url.params.multi_items())
        return httpx2.Response(200, json=payload, request=request)

    real_client = httpx2.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx2.MockTransport(respond),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert session.stats() == payload

    assert sent == [("view", "stats")]


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [_STATS_PAYLOAD, _GPU_STATS_PAYLOAD])
async def test_async_stats_preserves_response_shape(payload: dict[str, Any]) -> None:
    """Async stats returns the decoded platform response."""
    sent: list[tuple[str, str]] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        sent.extend(request.url.params.multi_items())
        return httpx2.Response(200, json=payload, request=request)

    real_async_client = httpx2.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx2.MockTransport(respond),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.stats() == payload

    assert sent == [("view", "stats")]


@pytest.mark.parametrize("field", ["kind", "status"])
def test_sync_fetch_rejects_invalid_filter(field: str) -> None:
    """Invalid Session filters fail at the synchronous public boundary."""
    with (
        Session(token=SecretStr("token"), url="https://example.test") as session,
        pytest.raises(ValidationError),
    ):
        session.fetch(**{field: "invalid"})


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["kind", "status"])
async def test_async_fetch_rejects_invalid_filter(field: str) -> None:
    """Invalid Session filters fail at the asynchronous public boundary."""
    async with AsyncSession(
        token=SecretStr("token"), url="https://example.test"
    ) as session:
        with pytest.raises(ValidationError):
            await session.fetch(**{field: "invalid"})
