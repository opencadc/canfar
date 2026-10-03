"""HTTP hooks log one line per response at INFO and full exchanges at DEBUG."""

from __future__ import annotations

import logging
from unittest.mock import patch

import httpx2
import pytest
from pydantic import SecretStr

from canfar.client import HTTPClient


@pytest.mark.asyncio
async def test_http_debug_hooks_log_url_and_response(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Sync and async clients log query URL plus response at DEBUG."""

    def respond(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json=[{"id": "abc"}],
            request=request,
        )

    base_url = "https://example.test/skaha/v0/"
    transport = httpx2.MockTransport(respond)
    real_client = httpx2.Client
    real_async_client = httpx2.AsyncClient

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

    records = [
        record for record in caplog.records if record.name == "canfar.hooks.httpx.debug"
    ]
    summaries = [r.getMessage() for r in records if r.levelno == logging.INFO]
    details = [r.getMessage() for r in records if r.levelno == logging.DEBUG]

    # INFO is one redacted line per response, as `canfar -v` shows it.
    assert summaries == ["GET https://example.test/skaha/v0/session -> 200"] * 2
    # DEBUG adds the full request URL and the response body.
    assert (
        sum(
            1
            for message in details
            if message.startswith("GET ") and "session?status=Running" in message
        )
        == 2
    )
    assert (
        sum(
            1
            for message in details
            if message.startswith("HTTP STATUS CODE -> 200") and '"id"' in message
        )
        == 2
    )
