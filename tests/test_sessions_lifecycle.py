"""Paired public contracts for synchronous and asynchronous Session lifecycle."""

from __future__ import annotations

from inspect import signature
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.sessions import AsyncSession, Session, connection_url

_BASE_URL = "https://example.test/skaha/v1/"
_CONNECT_IDS = ["missing", "stopped", "running", "terminating", "no-url"]
_EXPECTED_OPEN_URL = "https://example.test/running"

_EXPECTED_SESSION_SIGNATURES: dict[str, str] = {
    "fetch": (
        "(self, kind: 'Kind | None' = None, "
        "status: 'Status | None' = None, "
        "view: 'View | None' = None) -> 'list[dict[str, str]]'"
    ),
    "stats": "(self) -> 'dict[str, Any]'",
    "info": "(self, ids: 'list[str] | str') -> 'list[dict[str, Any]]'",
    "logs": (
        "(self, ids: 'list[str] | str', verbose: 'bool' = False) "
        "-> 'dict[str, str] | None'"
    ),
    "create": (
        "(self, name: 'str | CreateRequest', image: 'str | None' = None, "
        "cores: 'int | None' = None, ram: 'int | None' = None, "
        "kind: 'Kind' = 'headless', gpu: 'int | None' = None, "
        "cmd: 'str | None' = None, args: 'str | None' = None, "
        "env: 'dict[str, Any] | None' = None, replicas: 'int' = 1) "
        "-> 'list[str]'"
    ),
    "events": (
        "(self, ids: 'str | list[str]', verbose: 'bool' = False) "
        "-> 'list[dict[str, str]] | None'"
    ),
    "destroy": "(self, ids: 'str | list[str]') -> 'dict[str, bool]'",
    "destroy_with": (
        "(self, prefix: 'str', *, kind: 'Kind' = 'headless', "
        "status: 'Status' = 'Completed') -> 'dict[str, bool]'"
    ),
    "connect": "(self, ids: 'list[str] | str') -> 'None'",
}


@pytest.mark.parametrize(
    ("method", "expected"),
    list(_EXPECTED_SESSION_SIGNATURES.items()),
    ids=list(_EXPECTED_SESSION_SIGNATURES),
)
def test_session_signatures_are_stable_and_parallel(
    method: str,
    expected: str,
) -> None:
    """Sync and async Session methods keep the complete released contract."""
    sync_signature = signature(getattr(Session, method))
    assert str(sync_signature) == expected
    assert signature(getattr(AsyncSession, method)) == sync_signature


@pytest.mark.parametrize(
    ("record", "expected"),
    [
        ({"id": "missing"}, None),
        (
            {
                "id": "stopped",
                "status": "Stopped",
                "connectURL": "https://example.test/stopped",
            },
            None,
        ),
        (
            {
                "id": "running",
                "status": "Running",
                "connectURL": "https://example.test/running",
            },
            "https://example.test/running",
        ),
        (
            {
                "id": "terminating",
                "status": "Terminating",
                "connectURL": "https://example.test/terminating",
            },
            None,
        ),
    ],
)
def test_connection_url_is_the_shared_eligibility_policy(
    record: dict[str, str], expected: str | None
) -> None:
    """Only a running Session with a URL is eligible to connect."""
    assert connection_url(record) == expected


def _respond(request: httpx.Request) -> httpx.Response:
    """Return deterministic lifecycle payloads from one public transport."""
    if request.url.path.endswith("/session"):
        return httpx.Response(
            200,
            json=[
                {"id": "batch-1", "name": "batch-1"},
                {"id": "other", "name": "other-batch"},
            ],
            request=request,
        )

    session_id = request.url.path.rsplit("/", 1)[-1]
    if session_id in {"failed", "missing"}:
        message = "connection refused"
        raise httpx.ConnectError(message, request=request)
    if request.method == "DELETE":
        return httpx.Response(204, request=request)
    if request.url.params.get("view") == "events":
        return httpx.Response(200, text=f"event-{session_id}", request=request)

    records: dict[str, dict[str, Any]] = {
        "stopped": {
            "id": "stopped",
            "status": "Stopped",
            "connectURL": "https://example.test/stopped",
        },
        "running": {
            "id": "running",
            "status": "Running",
            "connectURL": _EXPECTED_OPEN_URL,
        },
        "terminating": {
            "id": "terminating",
            "status": "Terminating",
            "connectURL": "https://example.test/terminating",
        },
        "no-url": {"id": "no-url", "status": "Running"},
    }
    return httpx.Response(200, json=records[session_id], request=request)


def _filtered_destroy_responder(requests: list[httpx.Request]):
    """Record the filtered list request and accept its matching deletion."""

    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path.endswith("/session"):
            requests.append(request)
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "batch-1",
                        "name": "batch-1",
                        "kind": "headless",
                        "status": "Running",
                    }
                ],
                request=request,
            )
        if request.method == "DELETE":
            return httpx.Response(204, request=request)
        message = f"Unexpected request: {request.method} {request.url}"
        raise AssertionError(message)

    return respond


def test_sync_lifecycle_share_public_policy() -> None:
    """Sync events, destruction, selection, and connection share one policy."""
    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(_respond),
                **kwargs,
            ),
        ),
        patch("canfar.sessions.open_new_tab") as open_tab,
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        ids = ["one", "failed", "three"]
        assert session.events(ids) == [
            {"one": "event-one"},
            {"three": "event-three"},
        ]
        assert session.events("running", verbose=True) is None
        assert session.destroy(ids) == {
            "one": True,
            "failed": False,
            "three": True,
        }
        assert session.destroy_with("batch") == {"batch-1": True}
        assert session.destroy_with("other-.*") == {"other": True}
        session.connect(_CONNECT_IDS)
        session.connect("running")

    assert [call.args[0] for call in open_tab.call_args_list] == [
        _EXPECTED_OPEN_URL,
        _EXPECTED_OPEN_URL,
    ]


@pytest.mark.asyncio
async def test_async_lifecycle_share_public_policy() -> None:
    """Async events, destruction, selection, and connection share one policy."""
    real_async_client = httpx.AsyncClient
    with (
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: real_async_client(
                transport=httpx.MockTransport(_respond),
                **kwargs,
            ),
        ),
        patch("canfar.sessions.open_new_tab") as open_tab,
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            ids = ["one", "failed", "three"]
            assert await session.events(ids) == [
                {"one": "event-one"},
                {"three": "event-three"},
            ]
            assert await session.events("running", verbose=True) is None
            assert await session.destroy(ids) == {
                "one": True,
                "failed": False,
                "three": True,
            }
            assert await session.destroy_with("batch") == {"batch-1": True}
            assert await session.destroy_with("other-.*") == {"other": True}
            await session.connect(_CONNECT_IDS)

            await session.connect("running")

    assert [call.args[0] for call in open_tab.call_args_list] == [
        _EXPECTED_OPEN_URL,
        _EXPECTED_OPEN_URL,
    ]


def test_sync_destroy_with_passes_kind_and_status_filters() -> None:
    """Sync destroy_with forwards its filter keywords to Session.fetch."""
    requests: list[httpx.Request] = []
    real_client = httpx.Client
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(
                transport=httpx.MockTransport(_filtered_destroy_responder(requests)),
                **kwargs,
            ),
        ),
        Session(token=SecretStr("token"), url=_BASE_URL) as session,
    ):
        assert session.destroy_with("batch", kind="headless", status="Running") == {
            "batch-1": True
        }

    assert requests[0].url.params.multi_items() == [
        ("type", "headless"),
        ("status", "Running"),
    ]


@pytest.mark.asyncio
async def test_async_destroy_with_passes_kind_and_status_filters() -> None:
    """Async destroy_with forwards its filter keywords to Session.fetch."""
    requests: list[httpx.Request] = []
    real_async_client = httpx.AsyncClient
    with patch(
        "canfar.client.AsyncClient",
        side_effect=lambda **kwargs: real_async_client(
            transport=httpx.MockTransport(_filtered_destroy_responder(requests)),
            **kwargs,
        ),
    ):
        async with AsyncSession(token=SecretStr("token"), url=_BASE_URL) as session:
            assert await session.destroy_with(
                "batch", kind="headless", status="Running"
            ) == {"batch-1": True}

    assert requests[0].url.params.multi_items() == [
        ("type", "headless"),
        ("status", "Running"),
    ]
