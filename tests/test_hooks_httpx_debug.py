"""HTTP debug hooks log request URL and response body at DEBUG."""

from __future__ import annotations

import logging
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.client import HTTPClient


@pytest.mark.asyncio
async def test_http_debug_hooks_log_url_and_response(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Sync and async clients log query URL plus response at DEBUG."""

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"id": "abc"}],
            request=request,
        )

    base_url = "https://example.test/skaha/v0/"
    transport = httpx.MockTransport(respond)
    real_client = httpx.Client
    real_async_client = httpx.AsyncClient

    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(transport=transport, **kwargs),
        ),
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: real_async_client(
                transport=transport,
                **kwargs,
            ),
        ),
        caplog.at_level(logging.DEBUG, logger="canfar.hooks.httpx.debug"),
        HTTPClient(token=SecretStr("token"), url=base_url) as client,
    ):
        client.client.get("session", params={"status": "Running"})
        async with HTTPClient(token=SecretStr("token"), url=base_url) as aclient:
            await aclient.asynclient.get("session", params={"status": "Running"})

    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == "canfar.hooks.httpx.debug"
    ]
    assert any(
        message.startswith("GET ") and "session?status=Running" in message
        for message in messages
    )
    assert any(
        message.startswith("HTTP STATUS CODE -> 200")
        and '"id"' in message
        and "abc" in message
        for message in messages
    )
    assert sum(1 for message in messages if message.startswith("GET ")) == 2
    assert (
        sum(1 for message in messages if message.startswith("HTTP STATUS CODE -> 200"))
        == 2
    )
