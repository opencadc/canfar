"""Test Canfar Overview API."""

import pytest

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
