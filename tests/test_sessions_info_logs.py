"""Paired public contracts for synchronous and asynchronous Session reads."""

from __future__ import annotations

import logging
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.sessions import AsyncSession, Session

_BASE_URL = "https://example.test/skaha/v1/"

_INFO_LOG_CASES = (
    pytest.param([], [], {}, id="empty"),
    pytest.param("one", [{"id": "one"}], {"one": "log-one"}, id="one"),
    pytest.param(
        ["one", "two"],
        [{"id": "one"}, {"id": "two"}],
        {"one": "log-one", "two": "log-two"},
        id="many",
    ),
    pytest.param(
        ["one", "failed", "three"],
        [{"id": "one"}, {"id": "three"}],
        {"one": "log-one", "three": "log-three"},
        id="mixed-failure",
    ),
)


def _respond(request: httpx.Request) -> httpx.Response:
    """Return deterministic info/log payloads or one transport failure."""
    session_id = request.url.path.rsplit("/", 1)[-1]
    if session_id == "failed":
        message = "connection refused"
        raise httpx.ConnectError(message, request=request)
    if request.url.params.get("view") == "logs":
        return httpx.Response(200, text=f"log-{session_id}", request=request)
    return httpx.Response(200, json={"id": session_id}, request=request)


def _verbose_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return only Session logger messages captured for verbose output."""
    return [
        record.getMessage()
        for record in caplog.records
        if record.name == "canfar.sessions" and record.levelno == logging.INFO
    ]


@pytest.mark.parametrize(
    ("ids", "expected_info", "expected_logs"),
    _INFO_LOG_CASES,
)
def test_sync_info_and_logs_share_public_policy(
    ids: str | list[str],
    expected_info: list[dict[str, str]],
    expected_logs: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Sync info/logs preserve shape, order, failures, and verbose routing."""
    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(_respond),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert session.info(ids) == expected_info
        assert session.logs(ids) == expected_logs

        caplog.set_level(logging.INFO, logger="canfar.sessions")
        caplog.clear()
        assert session.logs(ids, verbose=True) is None
        sync_messages = _verbose_messages(caplog)

    assert sync_messages == [
        message
        for session_id, message in expected_logs.items()
        for message in (f"Session ID: {session_id}\n", message)
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("ids", "expected_info", "expected_logs"),
    _INFO_LOG_CASES,
)
async def test_async_info_and_logs_share_public_policy(
    ids: str | list[str],
    expected_info: list[dict[str, str]],
    expected_logs: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Async info/logs preserve shape, order, failures, and verbose routing."""
    real_async_client = httpx.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(_respond),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.info(ids) == expected_info
            assert await session.logs(ids) == expected_logs

            caplog.set_level(logging.INFO, logger="canfar.sessions")
            caplog.clear()
            assert await session.logs(ids, verbose=True) is None
            async_messages = _verbose_messages(caplog)

    assert async_messages == [
        message
        for session_id, message in expected_logs.items()
        for message in (f"Session ID: {session_id}\n", message)
    ]
