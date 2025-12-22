"""Test Canfar Session API."""

from time import sleep, time
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from canfar.models.session import CreateRequest
from canfar.sessions import Session

pytest.IDENTITY: list[str] = []


@pytest.fixture(scope="module")
def name():
    """Return a random name."""
    return str(uuid4().hex[:7])


@pytest.fixture(scope="session")
def session():
    """Test images."""
    session = Session()
    yield session
    del session


def test_fetch_with_kind(session: Session) -> None:
    """Test fetching images with kind."""
    session.fetch(kind="headless")


def test_fetch_malformed_kind(session: Session) -> None:
    """Test fetching images with malformed kind."""
    with pytest.raises(ValidationError):
        session.fetch(kind="invalid")


def test_fetch_with_malformed_view(session: Session) -> None:
    """Test fetching images with malformed view."""
    with pytest.raises(ValidationError):
        session.fetch(view="invalid")


def test_fetch_with_malformed_status(session: Session) -> None:
    """Test fetching images with malformed status."""
    with pytest.raises(ValidationError):
        session.fetch(status="invalid")


@pytest.mark.slow
def test_session_stats(session: Session) -> None:
    """Test fetching stats with kind."""
    assert "cores" in session.stats()
    assert "ram" in session.stats()


def test_create_session_with_malformed_kind(session: Session, name: str) -> None:
    """Test creating a session with malformed kind."""
    with pytest.raises(ValidationError):
        session.create(
            name=name,
            kind="invalid",
            image="ubuntu:latest",
            cmd="bash",
            replicas=1,
        )


def test_create_session_cmd_without_headless(session: Session, name: str) -> None:
    """Test creating a session without headless."""
    with pytest.raises(ValidationError):
        session.create(
            name=name,
            kind="notebook",
            image="ubuntu:latest",
            cmd="bash",
            replicas=1,
        )


@pytest.mark.slow
def test_create_session(session: Session, name: str) -> None:
    """Test creating a session."""
    identity: list[str] = session.create(
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


@pytest.mark.slow
def test_get_session_info(session: Session) -> None:
    """Test getting session info."""
    info: list[dict[str, Any]] = [{}]
    limit = time() + 60  # 1 minute
    success: bool = False
    while time() < limit:
        sleep(1)
        info = session.info(pytest.IDENTITY)
        if len(info) == 1:
            success = True
            break
    assert success, "Session info not found."


@pytest.mark.slow
def test_session_logs(session: Session) -> None:
    """Test getting session logs."""
    limit = time() + 60  # 1 minute
    logs: dict[str, str] = {}
    while time() < limit:
        sleep(1)
        info = session.info(pytest.IDENTITY)
        if info[0]["status"] in ("Succeeded", "Completed"):
            logs = session.logs(pytest.IDENTITY)
    success = False
    for line in logs[pytest.IDENTITY[0]].split("\n"):
        if "TEST=test" in line:
            success = True
            break
    session.logs(pytest.IDENTITY, verbose=True)
    assert success


@pytest.mark.slow
def test_session_events(session: Session) -> None:
    """Test getting session events."""
    limit = time() + 60  # 1 minute
    events: list[dict[str, str]] = []
    while time() < limit:
        sleep(1)
        events = session.events(pytest.IDENTITY)
        if len(events) > 0:
            break
    assert pytest.IDENTITY[0] in events[0]


@pytest.mark.slow
def test_delete_session(session: Session, name: str) -> None:
    """Test deleting a session."""
    # Delete the session
    sleep(10)
    deletion = session.destroy_with(prefix=name)
    assert deletion == {pytest.IDENTITY[0]: True}


def test_destroy_with_regex_match(session: Session) -> None:
    """Regex pattern should match substring in session name."""
    mock_sessions = [
        {
            "id": "xyz789",
            "name": "shiny-was-here",
            "status": "Running",
            "kind": "headless",
        }
    ]
    pattern = ".*-was-"

    with (
        patch.object(Session, "fetch", return_value=mock_sessions) as mock_fetch,
        patch.object(Session, "destroy", return_value={"xyz789": True}) as mock_destroy,
    ):
        result = session.destroy_with(prefix=pattern, kind="headless", status="Running")

    mock_fetch.assert_called_once_with(kind="headless", status="Running")
    mock_destroy.assert_called_once_with(["xyz789"])
    assert result == {"xyz789": True}


def test_destroy_with_name_deprecation(session: Session) -> None:
    """Deprecated name parameter removed; retained for backward-compat check."""
    with pytest.raises(TypeError):
        session.destroy_with(name=".*-was-")  # type: ignore[arg-type]


def test_create_session_with_type_field(name: str) -> None:
    """Test creating a session and confirm kind field is changed to type."""
    specification: CreateRequest = CreateRequest(
        name=name,
        image="images.canfar.net/skaha/terminal:1.1.2",
        cores=1,
        ram=1,
        kind="headless",
        cmd="env",
        replicas=1,
        env={"TEST": "test"},
    )
    data: dict[str, Any] = specification.model_dump(exclude_none=True, by_alias=True)
    assert "type" in data
    assert data["type"] == "headless"
    assert "kind" not in data


def test_bad_repica_requests(session: Session) -> None:
    """Test error handling."""
    with pytest.raises(ValidationError):
        session.create(
            name="bad",
            kind="firefly",
            image="images.canfar.net/skaha/terminal:1.1.2",
            replicas=10,
        )
    with pytest.raises(ValidationError):
        session.create(
            name="bad",
            kind="desktop",
            image="images.canfar.net/skaha/terminal:1.1.2",
            replicas=513,
        )


# Unit tests for connect method (covers lines 369-374)
class TestSessionConnect:
    """Test the Session.connect method."""

    @patch("canfar.sessions.open_new_tab")
    @patch.object(Session, "info")
    def test_connect_single_session_string(self, mock_info, mock_open_tab) -> None:
        """Test connect with single session ID as string."""
        session = Session()

        # Mock the info method to return session data with connectURL
        mock_info.return_value = [
            {
                "id": "session-123",
                "status": "Running",
                "connectURL": "https://example.com/connect",
            }
        ]

        session.connect("session-123")

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-123"])

        # Verify open_new_tab was called with the connectURL
        mock_open_tab.assert_called_once_with("https://example.com/connect")

    @patch("canfar.sessions.open_new_tab")
    @patch.object(Session, "info")
    def test_connect_multiple_sessions_list(self, mock_info, mock_open_tab) -> None:
        """Test connect with multiple session IDs as list."""
        session = Session()

        # Mock the info method to return session data for all IDs
        mock_info.return_value = [
            {
                "id": "session-1",
                "status": "Running",
                "connectURL": "https://example.com/connect1",
            },
            {
                "id": "session-2",
                "status": "Running",
                "connectURL": "https://example.com/connect2",
            },
        ]

        session.connect(["session-1", "session-2"])

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-1", "session-2"])

        # Verify open_new_tab was called for each connectURL
        assert mock_open_tab.call_count == 2
        mock_open_tab.assert_any_call("https://example.com/connect1")
        mock_open_tab.assert_any_call("https://example.com/connect2")

    @patch("canfar.sessions.open_new_tab")
    @patch.object(Session, "info")
    def test_connect_empty_info_response(self, mock_info, mock_open_tab) -> None:
        """Test connect when info returns empty list."""
        session = Session()

        # Mock the info method to return empty list
        mock_info.return_value = []

        # Should not raise any exception, just do nothing
        session.connect("session-123")

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-123"])

        # Verify open_new_tab was not called
        mock_open_tab.assert_not_called()

    @patch("canfar.sessions.open_new_tab")
    @patch.object(Session, "info")
    def test_connect_missing_connect_url(self, mock_info, mock_open_tab) -> None:
        """Test connect when session info lacks connectURL."""
        session = Session()

        # Mock the info method to return session without connectURL
        mock_info.return_value = [{"id": "session-123", "status": "Running"}]

        # Should not raise any exception, just skip the session
        session.connect("session-123")

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-123"])

        # Verify open_new_tab was not called
        mock_open_tab.assert_not_called()

    @patch("canfar.sessions.open_new_tab")
    @patch.object(Session, "info")
    def test_connect_non_running_session(self, mock_info, mock_open_tab) -> None:
        """Test connect when session is not in Running status."""
        session = Session()

        # Mock the info method to return session with non-Running status
        mock_info.return_value = [
            {
                "id": "session-123",
                "status": "Pending",
                "connectURL": "https://example.com/connect",
            }
        ]

        # Should not raise any exception, just skip the session
        session.connect("session-123")

        # Verify info was called with the session ID list
        mock_info.assert_called_once_with(["session-123"])

        # Verify open_new_tab was not called because status is not Running
        mock_open_tab.assert_not_called()
