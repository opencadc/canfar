"""Test the async session."""

from asyncio import sleep
from time import time
from unittest.mock import patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from canfar.sessions import AsyncSession


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
            if status["status"] == "Completed":
                done = True
    deletion = await asession.destroy_with(prefix=name)
    assert deletion == {pytest.IDENTITY[0]: True}


# Unit tests for connect method (covers lines 798-804)
class TestAsyncSessionConnect:
    """Test the AsyncSession.connect method."""

    @patch("canfar.sessions.open_new_tab")
    @patch.object(AsyncSession, "info")
    @pytest.mark.asyncio
    async def test_connect_single_session_string(
        self, mock_info, mock_open_tab
    ) -> None:
        """Test connect with single session ID as string."""
        asession = AsyncSession()

        # Mock the info method to return session data with connectURL
        mock_info.return_value = [{"connectURL": "https://example.com/connect"}]

        await asession.connect("session-123")

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-123"])

        # Verify open_new_tab was called with the connectURL
        mock_open_tab.assert_called_once_with("https://example.com/connect")

    @patch("canfar.sessions.open_new_tab")
    @patch.object(AsyncSession, "info")
    @pytest.mark.asyncio
    async def test_connect_multiple_sessions_list(
        self, mock_info, mock_open_tab
    ) -> None:
        """Test connect with multiple session IDs as list."""
        asession = AsyncSession()

        # Mock the info method to return session data for all IDs
        mock_info.return_value = [
            {"sessionId": "session-1", "connectURL": "https://example.com/connect1"},
            {"sessionId": "session-2", "connectURL": "https://example.com/connect2"},
        ]

        await asession.connect(["session-1", "session-2"])

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-1", "session-2"])

        # Verify open_new_tab was called for each connectURL
        assert mock_open_tab.call_count == 2
        mock_open_tab.assert_any_call("https://example.com/connect1")
        mock_open_tab.assert_any_call("https://example.com/connect2")

    @patch("canfar.sessions.open_new_tab")
    @patch.object(AsyncSession, "info")
    @pytest.mark.asyncio
    async def test_connect_session_without_connect_url(
        self, mock_info, mock_open_tab
    ) -> None:
        """Test connect when some sessions don't have connectURL."""
        asession = AsyncSession()

        # Mock the info method to return mixed session data
        mock_info.return_value = [
            {"sessionId": "session-1", "connectURL": "https://example.com/connect1"},
            {"sessionId": "session-2", "status": "Running"},  # No connectURL
            {"sessionId": "session-3", "connectURL": "https://example.com/connect3"},
        ]

        await asession.connect(["session-1", "session-2", "session-3"])

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-1", "session-2", "session-3"])

        # Verify open_new_tab was called only for sessions with connectURL
        assert mock_open_tab.call_count == 2
        mock_open_tab.assert_any_call("https://example.com/connect1")
        mock_open_tab.assert_any_call("https://example.com/connect3")
        # session-2 should be skipped because it has no connectURL

    @patch("canfar.sessions.open_new_tab")
    @patch.object(AsyncSession, "info")
    @pytest.mark.asyncio
    async def test_connect_string_to_list_conversion(
        self, mock_info, mock_open_tab
    ) -> None:
        """Test that single string ID is converted to list internally."""
        asession = AsyncSession()

        # Mock the info method
        mock_info.return_value = [{"connectURL": "https://example.com/connect"}]

        # Call with string (should be converted to list internally)
        await asession.connect("session-123")

        # The method should have processed it as a single-item list
        mock_info.assert_called_once_with(["session-123"])
        mock_open_tab.assert_called_once_with("https://example.com/connect")

    @patch("canfar.sessions.open_new_tab")
    @patch.object(AsyncSession, "info")
    @pytest.mark.asyncio
    async def test_connect_empty_info_response(self, mock_info, mock_open_tab) -> None:
        """Test connect when info returns empty list."""
        asession = AsyncSession()

        # Mock the info method to return empty list
        mock_info.return_value = []

        # Should not raise any exception, just do nothing
        await asession.connect("session-123")

        # Verify info was called
        mock_info.assert_called_once_with(["session-123"])

        # Verify open_new_tab was not called
        mock_open_tab.assert_not_called()
