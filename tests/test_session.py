"""Test Skaha Session API."""

from time import sleep, time
from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from skaha.models.session import CreateRequest
from skaha.session import Session

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
    """Test fetching images with kind."""
    assert "instances" in session.stats()


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
        if info[0]["status"] == "Succeeded":
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
