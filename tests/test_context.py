"""Test Canfar Context API."""

import httpx2
import pytest
from pydantic import SecretStr

from canfar.context import Context


@pytest.fixture(scope="session")
def context():
    """Test Context."""
    context = Context()
    try:
        yield context
    finally:
        context.__exit__(None, None, None)


@pytest.mark.integration
@pytest.mark.slow
def test_context(context) -> None:
    """Test context fetch."""
    assert "cores" in context.resources()


def test_context_resources_use_http_client() -> None:
    """Resources returns decoded context payload."""
    requests: list[httpx2.Request] = []

    def respond(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(
            200,
            json={"cores": {"default": 1}},
            request=request,
        )

    with (
        pytest.MonkeyPatch.context() as monkeypatch,
        Context(
            token=SecretStr("token"), url="https://example.test/skaha/v1"
        ) as context,
    ):
        monkeypatch.setattr(
            "canfar.client.Client",
            lambda **kwargs: httpx2.Client(
                transport=httpx2.MockTransport(respond), **kwargs
            ),
        )
        # The client is lazy, so the transport is installed before the request.
        assert context.resources() == {"cores": {"default": 1}}

    assert len(requests) == 1
    assert requests[0].url.path.endswith("/context")


def test_context_resources_raise_for_error_status_without_error_hooks() -> None:
    """A client without error hooks still reports a missing context endpoint."""
    with (
        pytest.MonkeyPatch.context() as monkeypatch,
        Context(
            token=SecretStr("token"),
            url="https://example.test/skaha/v1",
            raise_http_errors=False,
        ) as context,
    ):
        monkeypatch.setattr(
            "canfar.client.Client",
            lambda **kwargs: httpx2.Client(
                transport=httpx2.MockTransport(
                    lambda request: httpx2.Response(404, request=request)
                ),
                **kwargs,
            ),
        )

        with pytest.raises(httpx2.HTTPStatusError):
            context.resources()
