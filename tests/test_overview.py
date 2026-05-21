"""Test Canfar Overview API."""

from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.overview import Overview


@pytest.fixture(scope="session")
def overview():
    """Test overview."""
    overview = Overview()
    yield overview
    del overview


@pytest.mark.integration
@pytest.mark.slow
def test_available(overview: Overview) -> None:
    """Test available."""
    assert overview.availability(), "Server should be available"


def _sync_response(text: str) -> MagicMock:
    response = MagicMock()
    response.text = text
    return response


def test_overview_updates_base_url_and_parses_availability() -> None:
    """Overview strips version from base URL and parses available true."""
    sync_client = MagicMock()
    sync_client.base_url = httpx.URL("https://example.test/skaha/v1/")
    async_client = MagicMock()
    async_client.base_url = httpx.URL("https://example.test/skaha/v1/")
    sync_client.get.return_value = _sync_response(
        '<vosi:availability xmlns:vosi="http://www.ivoa.net/xml/'
        'VOSIAvailability/v1.0"><vosi:available>true</vosi:available>'
        "<vosi:note>ok</vosi:note></vosi:availability>"
    )

    with (
        patch("canfar.client.HTTPClient._create_sync_client", return_value=sync_client),
        patch(
            "canfar.client.HTTPClient._create_async_client", return_value=async_client
        ),
    ):
        overview = Overview(
            token=SecretStr("token"), url="https://example.test/skaha/v1"
        )

    assert str(overview.client.base_url) == "https://example.test/skaha"
    assert str(overview.asynclient.base_url) == "https://example.test/skaha"
    assert overview.availability() is True


def test_overview_availability_false_paths() -> None:
    """Overview availability returns false for empty or unavailable responses."""
    overview = Overview.model_construct()
    client = MagicMock()
    overview._client = client  # noqa: SLF001

    client.get.return_value = _sync_response("")
    assert overview.availability() is False

    client.get.return_value = _sync_response(
        '<vosi:availability xmlns:vosi="http://www.ivoa.net/xml/'
        'VOSIAvailability/v1.0"><vosi:note>missing</vosi:note></vosi:availability>'
    )
    assert overview.availability() is False

    client.get.return_value = _sync_response(
        '<vosi:availability xmlns:vosi="http://www.ivoa.net/xml/'
        'VOSIAvailability/v1.0"><vosi:available>false</vosi:available>'
        "</vosi:availability>"
    )
    assert overview.availability() is False
