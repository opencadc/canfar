"""Public Session.create request and failure contracts."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr, ValidationError

from canfar.models.session import CreateRequest
from canfar.sessions import AsyncSession, Session

if TYPE_CHECKING:
    from collections.abc import Collection

_BASE_URL = "https://example.test/skaha/v1/"
_SERIALIZED_REQUEST = [
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
]
_SERIALIZED_REQUEST_REPLICA_TWO = [
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
]
_FAILURE_CASES = (
    pytest.param(frozenset({"batch-2"}), ("batch-1-id",), id="partial"),
    pytest.param(frozenset({"batch-1", "batch-2"}), (), id="total"),
)
_INVALID_REQUEST_CASES = (
    pytest.param(
        (("kind", "invalid"), ("image", "skaha/terminal:latest")),
        id="invalid-kind",
    ),
    pytest.param(
        (
            ("kind", "notebook"),
            ("image", "skaha/terminal:latest"),
            ("cmd", "python"),
        ),
        id="notebook-command",
    ),
    pytest.param(
        (
            ("kind", "headless"),
            ("image", "skaha/terminal:latest"),
            ("replicas", 0),
        ),
        id="zero-replicas",
    ),
    pytest.param(
        (
            ("kind", "headless"),
            ("image", "skaha/terminal:latest"),
            ("replicas", 513),
        ),
        id="too-many-replicas",
    ),
)


def _create_request() -> CreateRequest:
    """Return one deterministic two-replica request."""
    return CreateRequest(
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


def _create_responder(sent: list[list[tuple[str, str]]]):
    """Return a transport handler that records and identifies replicas."""

    def respond(request: httpx.Request) -> httpx.Response:
        params = request.url.params.multi_items()
        sent.append(params)
        name = request.url.params["name"]
        return httpx.Response(200, text=f"{name}-id\n", request=request)

    return respond


def test_sync_create_serializes_the_public_request_contract() -> None:
    """Sync create serializes every replica through the HTTP boundary."""
    sent: list[list[tuple[str, str]]] = []
    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(_create_responder(sent)),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert session.create(_create_request()) == ["batch-1-id", "batch-2-id"]

    assert sent[0] == _SERIALIZED_REQUEST
    assert sent[1] == _SERIALIZED_REQUEST_REPLICA_TWO


@pytest.mark.asyncio
async def test_async_create_serializes_the_public_request_contract() -> None:
    """Async create serializes every replica through the HTTP boundary."""
    sent: list[list[tuple[str, str]]] = []
    real_async_client = httpx.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(_create_responder(sent)),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.create(_create_request()) == [
                "batch-1-id",
                "batch-2-id",
            ]

    assert sent[0] == _SERIALIZED_REQUEST
    assert sent[1] == _SERIALIZED_REQUEST_REPLICA_TWO


def _failure_responder(failed_names: Collection[str]):
    """Return a transport handler for partial or total replica failures."""

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

    return respond


@pytest.mark.parametrize(
    ("failed_names", "expected"),
    _FAILURE_CASES,
)
def test_sync_create_omits_failed_replicas(
    failed_names: frozenset[str], expected: tuple[str, ...]
) -> None:
    """Sync create omits failed replicas and returns an empty total failure."""
    request = CreateRequest(
        name="batch", image="skaha/terminal:latest", kind="headless", replicas=2
    )
    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(_failure_responder(failed_names)),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert session.create(request) == list(expected)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("failed_names", "expected"),
    _FAILURE_CASES,
)
async def test_async_create_omits_failed_replicas(
    failed_names: frozenset[str], expected: tuple[str, ...]
) -> None:
    """Async create omits failed replicas and returns an empty total failure."""
    request = CreateRequest(
        name="batch", image="skaha/terminal:latest", kind="headless", replicas=2
    )
    real_async_client = httpx.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(_failure_responder(failed_names)),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.create(request) == list(expected)


@pytest.mark.parametrize(
    "request_items",
    _INVALID_REQUEST_CASES,
)
def test_sync_create_rejects_invalid_requests(
    request_items: tuple[tuple[str, object], ...],
) -> None:
    """Invalid create requests fail before the synchronous HTTP boundary."""
    request_kwargs = dict(request_items)
    with (
        Session(token=SecretStr("token"), url="https://example.test") as session,
        pytest.raises(ValidationError),
    ):
        session.create(name="batch", **request_kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_items",
    _INVALID_REQUEST_CASES,
)
async def test_async_create_rejects_invalid_requests(
    request_items: tuple[tuple[str, object], ...],
) -> None:
    """Invalid create requests fail before the asynchronous HTTP boundary."""
    request_kwargs = dict(request_items)
    with pytest.raises(ValidationError):
        async with AsyncSession(
            token=SecretStr("token"), url="https://example.test"
        ) as session:
            await session.create(name="batch", **request_kwargs)


def _failure_log_responder(request: httpx.Request) -> httpx.Response:
    """Raise one safe-to-log HTTP failure for a create request."""
    response = httpx.Response(500, request=request, text="no capacity")
    message = "server error"
    raise httpx.HTTPStatusError(message, request=request, response=response)


def _assert_safe_create_log(caplog: pytest.LogCaptureFixture, secret: str) -> None:
    """Assert create logs only stable replica context and exception type."""
    logged = caplog.text
    assert secret not in logged
    assert "no capacity" not in logged
    assert "server error" not in logged
    assert "Failed to create session" in logged
    assert "replica 1/1" in logged
    assert "HTTPStatusError" in logged


def test_sync_create_failure_logs_only_safe_replica_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Sync create omits request payload and raw exception from logs."""
    environment_secret = "sync-create-environment-secret"
    caplog.set_level(logging.ERROR, logger="canfar.sessions")
    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(_failure_log_responder),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert (
            session.create(
                name="test-name",
                image="images.example/net/img:latest",
                kind="headless",
                env={"ACCESS_TOKEN": environment_secret},
                replicas=1,
            )
            == []
        )

    _assert_safe_create_log(caplog, environment_secret)


@pytest.mark.asyncio
async def test_async_create_failure_logs_only_safe_replica_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Async create omits request payload and raw exception from logs."""
    environment_secret = "async-create-environment-secret"
    caplog.set_level(logging.ERROR, logger="canfar.sessions")
    real_async_client = httpx.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(_failure_log_responder),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert (
                await session.create(
                    name="test-name",
                    image="images.example/net/img:latest",
                    kind="headless",
                    env={"REFRESH_TOKEN": environment_secret},
                    replicas=1,
                )
                == []
            )

    _assert_safe_create_log(caplog, environment_secret)
