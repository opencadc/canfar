"""Test Canfar Discover API."""

import pytest

from canfar.models.registry import IVOARegistrySearch
from canfar.utils.discover import Discover


@pytest.fixture
async def discover():
    """Test discover."""
    config = IVOARegistrySearch()

    async with Discover(config, timeout=2, max_connections=100) as discovery:
        yield discovery


@pytest.mark.asyncio
async def test_discover(discover: Discover) -> None:
    """Test discover."""
    assert discover is not None
    assert discover.config is not None
    assert discover.timeout == 2


@pytest.mark.asyncio
async def test_functionality(discover: Discover) -> None:
    """Test functionality."""
    results = await discover.servers()
    assert results is not None
    assert results.endpoints is not None
    assert results.total_time is not None
    assert results.registry_fetch_time is not None
    assert results.endpoint_check_time is not None
    assert results.found is not None
    assert results.checked is not None
    assert results.successful is not None
