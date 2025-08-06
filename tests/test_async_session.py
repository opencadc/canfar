"""Test the async session."""

from asyncio import sleep
from time import time
from uuid import uuid4

import pytest
from pydantic import ValidationError

from skaha.session import AsyncSession


@pytest.fixture(scope="module")
def name():
    """Return a random name."""
    return str(uuid4().hex[:7])


@pytest.fixture
def asession():
    """Test images."""
    return AsyncSession()


@pytest.mark.asyncio
async def test_fetch_with_kind(asession: AsyncSession) -> None:
    """Test fetching images with kind."""
    await asession.fetch(kind="headless")


@pytest.mark.asyncio
async def test_fetch_malformed_kind(asession: AsyncSession) -> None:
    """Test fetching images with malformed kind."""
    with pytest.raises(ValidationError):
        await asession.fetch(kind="invalid")


@pytest.mark.asyncio
async def test_fetch_with_malformed_view(asession: AsyncSession) -> None:
    """Test fetching images with malformed view."""
    with pytest.raises(ValidationError):
        await asession.fetch(view="invalid")


@pytest.mark.asyncio
@pytest.mark.slow
async def test_get_session_stats(asession: AsyncSession) -> None:
    """Test fetching images with kind."""
    response = await asession.stats()
    assert "instances" in response


@pytest.mark.asyncio
async def test_create_session_invalid(asession: AsyncSession, name: str) -> None:
    """Test creating a session with malformed kind."""
    with pytest.raises(ValidationError):
        await asession.create(
            name=name,
            kind="invalid",
            image="jupyter/base-notebook",
        )


@pytest.mark.asyncio
@pytest.mark.order(1)
@pytest.mark.slow
async def test_create_session(asession: AsyncSession, name: str) -> None:
    """Test creating a session."""
    identity: list[str] = await asession.create(
        name=name,
        kind="headless",
        cores=1,
        ram=1,
        image="images.canfar.net/skaha/terminal:1.1.2",
        cmd="env",
        replicas=1,
        env={"TEST": "test"},
    )
    assert len(identity) == 1
    assert identity[0] != ""
    pytest.IDENTITY = identity


@pytest.mark.asyncio
@pytest.mark.order(2)
@pytest.mark.slow
async def test_get_succeeded(asession: AsyncSession) -> None:
    """Test getting succeeded sessions."""
    limit: float = time() + 60  # 1 minute
    while time() < limit:
        response = await asession.fetch()
        for result in response:
            await sleep(1)
            if result["id"] == pytest.IDENTITY[0]:
                break


@pytest.mark.asyncio
@pytest.mark.order(3)
@pytest.mark.slow
async def test_get_logs(asession: AsyncSession) -> None:
    """Test getting logs for a session."""
    logs = await asession.logs(ids=pytest.IDENTITY)
    assert logs != ""
    assert "TEST" in logs[pytest.IDENTITY[0]]
    no_logs = await asession.logs(ids=pytest.IDENTITY, verbose=True)
    assert no_logs is None


@pytest.mark.asyncio
@pytest.mark.order(4)
@pytest.mark.slow
async def test_session_events(asession: AsyncSession) -> None:
    """Test getting session events."""
    done = False
    limit = time() + 60
    while not done and time() < limit:
        await sleep(1)
        events = await asession.events(pytest.IDENTITY)
        if events:
            done = True
            assert pytest.IDENTITY[0] in events[0]
    assert done, "No events found for the session."


@pytest.mark.asyncio
@pytest.mark.order(5)
@pytest.mark.slow
async def test_delete_session(asession: AsyncSession, name: str) -> None:
    """Test deleting a session."""
    # Delete the session
    done = False
    while not done:
        info = await asession.info(ids=pytest.IDENTITY)
        for status in info:
            if status["status"] == "Succeeded":
                done = True
    deletion = await asession.destroy_with(prefix=name)
    assert deletion == {pytest.IDENTITY[0]: True}
