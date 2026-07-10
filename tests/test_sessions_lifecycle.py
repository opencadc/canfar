"""Paired public contracts for synchronous and asynchronous Session lifecycle."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.sessions import AsyncSession, Session, connection_url


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


@pytest.mark.asyncio
async def test_sync_and_async_lifecycle_share_public_policy() -> None:
    """Events, destruction, selection, and connection have matching outcomes."""

    def respond(request: httpx.Request) -> httpx.Response:
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
                "connectURL": "https://example.test/running",
            },
            "terminating": {
                "id": "terminating",
                "status": "Terminating",
                "connectURL": "https://example.test/terminating",
            },
        }
        return httpx.Response(200, json=records[session_id], request=request)

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
        patch("canfar.sessions.open_new_tab") as open_tab,
        Session(token=SecretStr("token"), url=base_url) as session,
    ):
        async with AsyncSession(token=SecretStr("token"), url=base_url) as asession:
            ids = ["one", "failed", "three"]
            expected_events = [{"one": "event-one"}, {"three": "event-three"}]
            expected_destroy = {"one": True, "failed": False, "three": True}

            assert session.events(ids) == expected_events
            assert await asession.events(ids) == expected_events
            assert session.destroy(ids) == expected_destroy
            assert await asession.destroy(ids) == expected_destroy
            assert session.destroy_with("batch") == {"batch-1": True}
            assert await asession.destroy_with("batch") == {"batch-1": True}

            connect_ids = ["missing", "stopped", "running", "terminating"]
            session.connect(connect_ids)
            await asession.connect(connect_ids)

    assert [call.args[0] for call in open_tab.call_args_list] == [
        "https://example.test/running",
        "https://example.test/running",
    ]
