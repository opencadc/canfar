"""Credentialed Session lifecycle contracts.

These tests intentionally keep each live workflow self-contained.  They are
excluded from the deterministic local gate and require a configured CANFAR
Authentication Record.
"""

from __future__ import annotations

import asyncio
from time import monotonic, sleep
from uuid import uuid4

import pytest

from canfar.sessions import AsyncSession, Session


def _session_name() -> str:
    """Return a unique name for one credentialed lifecycle."""
    return f"contract-{uuid4().hex[:10]}"


@pytest.mark.integration
@pytest.mark.slow
def test_sync_session_lifecycle_is_self_contained() -> None:
    """Create, observe, and clean up one synchronous Session."""
    name = _session_name()
    identity: list[str] = []

    with Session() as session:
        try:
            identity = session.create(
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
            session_id = identity[0]

            deadline = monotonic() + 60
            info: list[dict[str, object]] = []
            while monotonic() < deadline:
                info = session.info(session_id)
                if info and info[0].get("status") in {"Succeeded", "Completed"}:
                    break
                sleep(1)
            assert info
            assert info[0].get("status") in {"Succeeded", "Completed"}

            logs = session.logs(session_id)
            assert logs is not None
            assert "TEST=test" in logs[session_id]
            events = session.events(session_id)
            assert any(session_id in event for event in events)
        finally:
            if identity:
                session.destroy(identity)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_async_session_lifecycle_is_self_contained() -> None:
    """Create, observe, and clean up one asynchronous Session."""
    name = _session_name()
    identity: list[str] = []

    async with AsyncSession() as session:
        try:
            identity = await session.create(
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
            session_id = identity[0]

            deadline = monotonic() + 60
            info: list[dict[str, object]] = []
            while monotonic() < deadline:
                info = await session.info(session_id)
                if info and info[0].get("status") in {"Succeeded", "Completed"}:
                    break
                await asyncio.sleep(1)
            assert info
            assert info[0].get("status") in {"Succeeded", "Completed"}

            logs = await session.logs(session_id)
            assert logs is not None
            assert "TEST=test" in logs[session_id]
            events = await session.events(session_id)
            assert any(session_id in event for event in events)
        finally:
            if identity:
                await session.destroy(identity)
