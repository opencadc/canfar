"""What the Science Platform receives for batch Sessions."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import httpx2
import pytest
from pydantic import SecretStr, ValidationError

from canfar.exceptions.session import SessionRequestError
from canfar.sessions import AsyncSession, Session

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

_BASE_URL = "https://example.test/skaha/v1/"
_BATCH = {
    "name": "field-reduction",
    "image": "skaha/astroml:latest",
    "kind": "batch",
    "replicas": 50,
    "cores": 1,
    "ram": 4,
    "cmd": "python",
    "args": "/arc/projects/demo/worker.py",
    "env": {"RUN_DIR": "/arc/projects/demo/runs/1"},
    "maxfail": 0.25,
}
_BATCH_FORM = sorted(
    [
        ("name", "field-reduction"),
        ("image", "images.canfar.net/skaha/astroml:latest"),
        ("cores", "1"),
        ("ram", "4"),
        ("type", "batch"),
        ("cmd", "python"),
        ("args", "/arc/projects/demo/worker.py"),
        ("replicas", "50"),
        ("maxfail", "0.25"),
        ("env", "RUN_DIR=/arc/projects/demo/runs/1"),
    ]
)
_BATCH_DOCUMENT = {
    "apiVersion": "canfar.net/v1alpha1",
    "kind": "Batch",
    "metadata": {"name": "k7nq2wpx"},
    "spec": {"replicas": 50, "maxfail": None},
    "status": {"phase": "Pending", "succeeded": 0, "failed": 0},
}


def _server(sent: list[httpx2.Request]) -> Callable[[httpx2.Request], httpx2.Response]:
    """Answer like Skaha's batch routes and record every request."""

    def respond(request: httpx2.Request) -> httpx2.Response:
        """Return the batch reply for one request."""
        sent.append(request)
        params = request.url.params
        if request.method == "POST":
            return httpx2.Response(200, text="k7nq2wpx\n", request=request)
        if params.get("view") == "logs":
            if "replica" not in params:
                return httpx2.Response(
                    400, json={"message": "replica is required"}, request=request
                )
            return httpx2.Response(
                200, text=f"log of replica {params['replica']}", request=request
            )
        if request.url.path.endswith("/session"):
            return httpx2.Response(200, json=[], request=request)
        return httpx2.Response(200, json=_BATCH_DOCUMENT, request=request)

    return respond


@pytest.fixture
def sent() -> Iterator[list[httpx2.Request]]:
    """Route both Session clients to the recording server."""
    requests: list[httpx2.Request] = []
    real_client, real_async_client = httpx2.Client, httpx2.AsyncClient
    transport = httpx2.MockTransport(_server(requests))
    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: real_client(transport=transport, **kwargs),
        ),
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: real_async_client(
                transport=transport, **kwargs
            ),
        ),
    ):
        yield requests


def _session() -> Session:
    """Return a sync client for the recording server."""
    return Session(token=SecretStr("token"), url=_BASE_URL)


def _async_session() -> AsyncSession:
    """Return an async client for the recording server."""
    return AsyncSession(token=SecretStr("token"), url=_BASE_URL)


def test_batch_create_sends_one_post_and_returns_one_id(
    sent: list[httpx2.Request],
) -> None:
    """A batch of 50 replicas is one create request with no replica variables."""
    with _session() as session:
        assert session.create(**_BATCH) == ["k7nq2wpx"]

    assert len(sent) == 1
    assert sorted(sent[0].url.params.multi_items()) == _BATCH_FORM


@pytest.mark.asyncio
async def test_async_batch_create_sends_one_post_and_returns_one_id(
    sent: list[httpx2.Request],
) -> None:
    """The async client sends the same single batch request."""
    async with _async_session() as session:
        assert await session.create(**_BATCH) == ["k7nq2wpx"]

    assert len(sent) == 1
    assert sorted(sent[0].url.params.multi_items()) == _BATCH_FORM


def test_batch_create_omits_unset_maxfail(sent: list[httpx2.Request]) -> None:
    """Leaving maxfail unset sends no maxfail field."""
    request = {key: value for key, value in _BATCH.items() if key != "maxfail"}
    with _session() as session:
        session.create(**request)

    assert "maxfail" not in sent[0].url.params


def test_reserved_environment_is_rejected_before_any_request(
    sent: list[httpx2.Request],
) -> None:
    """A CANFAR_ env name fails validation and nothing reaches the Server."""
    with _session() as session, pytest.raises(ValidationError, match="CANFAR_"):
        session.create(**{**_BATCH, "env": {"CANFAR_REPLICA_COUNT": "9"}})

    assert sent == []


def test_headless_replicas_warn_and_still_create_each_session(
    sent: list[httpx2.Request],
) -> None:
    """Headless replicas are deprecated but still one request per replica."""
    with (
        _session() as session,
        pytest.warns(FutureWarning, match="kind='batch'") as warned,
    ):
        ids = session.create(
            name="legacy", image="skaha/astroml", kind="headless", replicas=2
        )

    assert ids == ["k7nq2wpx", "k7nq2wpx"]
    assert [request.url.params["name"] for request in sent] == ["legacy-1", "legacy-2"]
    assert "REPLICA_ID=2" in sent[1].url.params.get_list("env")
    assert warned[0].filename == __file__


@pytest.mark.asyncio
async def test_async_headless_replicas_warn_at_the_caller(
    sent: list[httpx2.Request],
) -> None:
    """The async warning also points at the line that called create."""
    async with _async_session() as session:
        with pytest.warns(FutureWarning, match="kind='batch'") as warned:
            await session.create(
                name="legacy", image="skaha/astroml", kind="headless", replicas=3
            )

    assert len(sent) == 3
    assert warned[0].filename == __file__


def test_single_headless_session_does_not_warn(sent: list[httpx2.Request]) -> None:
    """One headless Session is not deprecated."""
    with _session() as session:
        session.create(name="one", image="skaha/astroml", kind="headless")

    assert len(sent) == 1


def test_logs_request_names_the_replica(sent: list[httpx2.Request]) -> None:
    """A replica log request carries the 0-based replica index."""
    with _session() as session:
        assert session.logs("k7nq2wpx", replica=0) == {"k7nq2wpx": "log of replica 0"}

    assert sent[0].url.params["replica"] == "0"


@pytest.mark.asyncio
async def test_async_logs_request_names_the_replica(
    sent: list[httpx2.Request],
) -> None:
    """The async client sends the same replica parameter."""
    async with _async_session() as session:
        assert await session.logs("k7nq2wpx", replica=49) == {
            "k7nq2wpx": "log of replica 49"
        }

    assert sent[0].url.params["replica"] == "49"


def test_batch_logs_without_replica_fail_like_any_http_error(
    sent: list[httpx2.Request],
) -> None:
    """The Server's 400 for a missing replica follows the errors policy."""
    with _session() as session, pytest.raises(SessionRequestError) as caught:
        session.logs("k7nq2wpx", errors="raise")

    assert "replica" not in sent[0].url.params
    error = caught.value.errors["k7nq2wpx"]
    assert isinstance(error, httpx2.HTTPStatusError)
    assert error.response.status_code == 400


def test_fetch_batch_filters_by_type(sent: list[httpx2.Request]) -> None:
    """Listing batches sends type=batch."""
    with _session() as session:
        session.fetch(kind="batch")

    assert sent[0].url.params["type"] == "batch"


def test_info_returns_the_batch_document_unchanged(
    sent: list[httpx2.Request],
) -> None:
    """Info hands back the Batch document as the Server sent it."""
    with _session() as session:
        assert session.info("k7nq2wpx") == [_BATCH_DOCUMENT]

    assert sent[0].url.path.endswith("/session/k7nq2wpx")
