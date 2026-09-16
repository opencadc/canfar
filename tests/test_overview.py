"""Test Canfar Overview API."""

import asyncio
from unittest.mock import patch

import httpx
import pytest
from pydantic import SecretStr

from canfar.overview import Overview


@pytest.fixture(scope="session")
def overview():
    """Test overview."""
    overview = Overview()
    try:
        yield overview
    finally:
        overview.__exit__(None, None, None)
        asyncio.run(overview.__aexit__(None, None, None))


@pytest.mark.integration
@pytest.mark.slow
def test_available(overview: Overview) -> None:
    """Test available."""
    assert overview.availability(), "Server should be available"


def test_overview_updates_base_url_and_parses_availability() -> None:
    """Overview strips version from base URL and parses available true."""
    payload = (
        '<vosi:availability xmlns:vosi="http://www.ivoa.net/xml/'
        'VOSIAvailability/v1.0"><vosi:available>true</vosi:available>'
        "<vosi:note>ok</vosi:note></vosi:availability>"
    )

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=payload, request=request)

    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: httpx.Client(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        ),
        patch(
            "canfar.client.AsyncClient",
            side_effect=lambda **kwargs: httpx.AsyncClient(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        ),
        Overview(
            token=SecretStr("token"), url="https://example.test/skaha/v1"
        ) as overview,
    ):
        try:
            assert str(overview.client.base_url) == "https://example.test/skaha/"
            assert str(overview.asynclient.base_url) == "https://example.test/skaha/"
            assert overview.availability() is True
        finally:
            asyncio.run(overview.__aexit__(None, None, None))


def test_overview_availability_false_paths() -> None:
    """Overview availability returns false for empty or unavailable responses."""
    responses = iter(
        [
            "",
            (
                '<vosi:availability xmlns:vosi="http://www.ivoa.net/xml/'
                'VOSIAvailability/v1.0"><vosi:note>missing</vosi:note>'
                "</vosi:availability>"
            ),
            (
                '<vosi:availability xmlns:vosi="http://www.ivoa.net/xml/'
                'VOSIAvailability/v1.0"><vosi:available>false</vosi:available>'
                "</vosi:availability>"
            ),
        ]
    )

    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=next(responses), request=request)

    with (
        patch(
            "canfar.client.Client",
            side_effect=lambda **kwargs: httpx.Client(
                transport=httpx.MockTransport(respond), **kwargs
            ),
        ),
        Overview(token=SecretStr("token"), url="https://example.test") as overview,
    ):
        try:
            assert overview.availability() is False
            assert overview.availability() is False
            assert overview.availability() is False
        finally:
            asyncio.run(overview.__aexit__(None, None, None))
