"""Test Canfar Context API."""

from unittest.mock import MagicMock

import pytest

from canfar.context import Context


@pytest.fixture(scope="session")
def context():
    """Test Context."""
    context = Context()
    yield context
    del context


@pytest.mark.integration
@pytest.mark.slow
def test_context(context) -> None:
    """Test context fetch."""
    assert "cores" in context.resources()


def test_context_resources_use_http_client() -> None:
    """Resources returns decoded context payload."""
    context = Context(token="token", url="https://example.test/skaha/v1")
    mock_client = MagicMock()
    mock_client.get.return_value.json.return_value = {"cores": {"default": 1}}
    context._client = mock_client  # noqa: SLF001

    assert context.resources() == {"cores": {"default": 1}}
    mock_client.get.assert_called_once_with(url="context")
