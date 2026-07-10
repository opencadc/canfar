"""Paired public contracts for synchronous and asynchronous Session reads."""

from __future__ import annotations

import logging
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.sessions import AsyncSession, Session


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("ids", "expected_info", "expected_logs"),
    [
        ([], [], {}),
        ("one", [{"id": "one"}], {"one": "log-one"}),
        (
            ["one", "two"],
            [{"id": "one"}, {"id": "two"}],
            {"one": "log-one", "two": "log-two"},
        ),
        (
            ["one", "failed", "three"],
            [{"id": "one"}, {"id": "three"}],
            {"one": "log-one", "three": "log-three"},
        ),
    ],
)
async def test_sync_and_async_info_and_logs_share_public_policy(
    ids: str | list[str],
    expected_info: list[dict[str, str]],
    expected_logs: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Zero, one, many, and mixed results have matching shape and order."""

    def respond(request: httpx.Request) -> httpx.Response:
        session_id = request.url.path.rsplit("/", 1)[-1]
        if session_id == "failed":
            message = "connection refused"
            raise httpx.ConnectError(message, request=request)
        if request.url.params.get("view") == "logs":
            return httpx.Response(
                200,
                text=f"log-{session_id}",
                request=request,
            )
        return httpx.Response(200, json={"id": session_id}, request=request)

    base_url = "https://example.test/skaha/v1/"
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
        Session(token=SecretStr("token"), url=base_url) as session,
    ):
        async with AsyncSession(token=SecretStr("token"), url=base_url) as asession:
            assert session.info(ids) == expected_info
            assert await asession.info(ids) == expected_info
            assert session.logs(ids) == expected_logs
            assert await asession.logs(ids) == expected_logs

            caplog.set_level(logging.INFO, logger="canfar.sessions")
            caplog.clear()
            assert session.logs(ids, verbose=True) is None
            sync_messages = [
                record.getMessage()
                for record in caplog.records
                if record.name == "canfar.sessions"
            ]
            caplog.clear()
            assert await asession.logs(ids, verbose=True) is None
            async_messages = [
                record.getMessage()
                for record in caplog.records
                if record.name == "canfar.sessions"
            ]
            assert sync_messages == async_messages
