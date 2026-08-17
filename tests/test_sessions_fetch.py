"""Paired public contracts for synchronous and asynchronous Session fetches."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.sessions import AsyncSession, Session


@pytest.mark.asyncio
async def test_sync_and_async_fetch_share_request_and_response_policy() -> None:
    """Fetch uses identical filters and preserves the server response shape."""
    sent: dict[str, list[tuple[str, str]]] = {"sync": [], "async": []}
    payload = [{"id": "session-1", "name": "notebook", "status": "Running"}]

    def handler(lane: str):
        def respond(request: httpx.Request) -> httpx.Response:
            sent[lane] = request.url.params.multi_items()
            return httpx.Response(200, json=payload, request=request)

        return respond

    base_url = "https://example.test/skaha/v1/"
    real_client = httpx.Client
    real_async_client = httpx.AsyncClient

    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(handler("sync")),
                **kwargs,
            ),
        ),
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: real_async_client(
                transport=httpx.MockTransport(handler("async")),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=base_url) as session,
    ):
        async with AsyncSession(token=SecretStr("token"), url=base_url) as asession:
            filters = {"kind": "notebook", "status": "Running", "view": "all"}
            assert session.fetch(**filters) == payload
            assert await asession.fetch(**filters) == payload

    expected = [("type", "notebook"), ("status", "Running"), ("view", "all")]
    assert sent == {"sync": expected, "async": expected}
