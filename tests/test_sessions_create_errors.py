"""Unit tests for Session.create and AsyncSession.create error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.models.session import CreateRequest
from canfar.sessions import AsyncSession, Session


def _http_status_error() -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "https://ws-uv.canfar.net/skaha/v1/session")
    response = httpx.Response(500, request=request, text="no capacity")
    return httpx.HTTPStatusError("server error", request=request, response=response)


@pytest.mark.asyncio
async def test_sync_and_async_create_serialize_the_same_request() -> None:
    """Both public clients serialize one CreateRequest identically."""
    sent: dict[str, list[list[tuple[str, str]]]] = {"sync": [], "async": []}

    def handler(lane: str):
        def respond(request: httpx.Request) -> httpx.Response:
            sent[lane].append(request.url.params.multi_items())
            name = request.url.params["name"]
            return httpx.Response(200, text=f"{name}-id\n", request=request)

        return respond

    request = CreateRequest(
        name="batch",
        image="custom/image:latest",
        cores=2,
        ram=4,
        kind="headless",
        gpus=1,
        cmd="python",
        args="-m worker",
        env={"A": "1"},
        replicas=2,
    )
    base_url = "https://example.test/skaha/v1/"
    real_client = httpx.Client
    real_async_client = httpx.AsyncClient
    sync_transport = httpx.MockTransport(handler("sync"))
    async_transport = httpx.MockTransport(handler("async"))

    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=sync_transport,
                **kwargs,
            ),
        ),
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: real_async_client(
                transport=async_transport,
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=base_url) as session,
    ):
        async with AsyncSession(token=SecretStr("token"), url=base_url) as asession:
            assert session.create(request) == ["batch-1-id", "batch-2-id"]
            assert await asession.create(request) == ["batch-1-id", "batch-2-id"]

    assert sent["sync"] == sent["async"]
    assert sent["sync"] == [
        [
            ("name", "batch-1"),
            ("image", "images.canfar.net/custom/image:latest"),
            ("cores", "2"),
            ("ram", "4"),
            ("type", "headless"),
            ("gpus", "1"),
            ("cmd", "python"),
            ("args", "-m worker"),
            ("env", "A=1"),
            ("env", "REPLICA_ID=1"),
            ("env", "REPLICA_COUNT=2"),
        ],
        [
            ("name", "batch-2"),
            ("image", "images.canfar.net/custom/image:latest"),
            ("cores", "2"),
            ("ram", "4"),
            ("type", "headless"),
            ("gpus", "1"),
            ("cmd", "python"),
            ("args", "-m worker"),
            ("env", "A=1"),
            ("env", "REPLICA_ID=2"),
            ("env", "REPLICA_COUNT=2"),
        ],
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failed_names", "expected"),
    [
        ({"batch-2"}, ["batch-1-id"]),
        ({"batch-1", "batch-2"}, []),
    ],
)
async def test_sync_and_async_create_share_http_failure_policy(
    failed_names: set[str],
    expected: list[str],
) -> None:
    """Per-replica HTTP failures are omitted and total failure returns empty."""

    def respond(request: httpx.Request) -> httpx.Response:
        name = request.url.params["name"]
        if name in failed_names:
            if len(failed_names) == 1:
                message = "connection refused"
                raise httpx.ConnectError(message, request=request)
            response = httpx.Response(503, request=request)
            message = "service unavailable"
            raise httpx.HTTPStatusError(
                message,
                request=request,
                response=response,
            )
        return httpx.Response(200, text=f"{name}-id\n", request=request)

    request = CreateRequest(
        name="batch",
        image="skaha/terminal:latest",
        kind="headless",
        replicas=2,
    )
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
            assert session.create(request) == expected
            assert await asession.create(request) == expected


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
