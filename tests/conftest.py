"""Shared pytest fixtures for deterministic CANFAR tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_REQUESTED_TEST_HOME = os.environ.get("CANFAR_TEST_HOME")
if _REQUESTED_TEST_HOME is None:
    _REQUESTED_TEST_HOME = tempfile.mkdtemp(prefix="canfar-test-home-")

ISOLATED_HOME = Path(_REQUESTED_TEST_HOME)
os.environ["CANFAR_TEST_HOME"] = _REQUESTED_TEST_HOME
os.environ["HOME"] = _REQUESTED_TEST_HOME
ISOLATED_HOME.mkdir(parents=True, exist_ok=True)


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """Ensure the isolated HOME exists before collection starts."""
    ISOLATED_HOME.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def isolate_canfar_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear CANFAR env overrides so tests do not depend on shell state."""
    for key in list(os.environ):
        if key.startswith("CANFAR_") and key != "CANFAR_TEST_HOME":
            monkeypatch.delenv(key, raising=False)
