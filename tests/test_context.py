"""Test Canfar Context API."""

import httpx
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
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
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
            lambda **kwargs: httpx.Client(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        )
        # The client is lazy, so the transport is installed before the request.
        assert context.resources() == {"cores": {"default": 1}}

    assert len(requests) == 1
    assert requests[0].url.path.endswith("/context")
