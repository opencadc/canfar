"""Unit tests for Session.create and AsyncSession.create error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from canfar.sessions import AsyncSession, Session


def _http_status_error() -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://ws-uv.canfar.net/skaha/v1/session")
    response = httpx.Response(500, request=request, text="no capacity")
    return httpx.HTTPStatusError("server error", request=request, response=response)


@patch("canfar.sessions._log_http_task_failure")
def test_sync_create_returns_empty_on_http_error(mock_log_fail: MagicMock) -> None:
    """Sync create returns [] and logs payload context when post fails."""
    session = Session()
    mock_client = MagicMock()
    mock_client.post.side_effect = _http_status_error()
    session._client = mock_client  # noqa: SLF001

    result = session.create(
        name="test-name",
        image="images.example/net/img:latest",
        kind="headless",
        replicas=1,
    )

    assert result == []
    mock_log_fail.assert_called_once()
    assert mock_log_fail.call_args[0][0] == "Failed to create session with payload"
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
@patch("canfar.sessions._log_http_task_failure")
async def test_async_create_empty_on_http_error(mock_log_fail: MagicMock) -> None:
    """Async create returns [] and logs payload context when post fails."""
    asession = AsyncSession()
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=_http_status_error())
    asession._asynclient = mock_client  # noqa: SLF001

    result = await asession.create(
        name="test-name",
        image="images.example/net/img:latest",
        kind="headless",
        replicas=1,
    )

    assert result == []
    mock_log_fail.assert_called_once()
    assert mock_log_fail.call_args[0][0] == "Failed to create session with payload"
    mock_client.post.assert_awaited_once()
