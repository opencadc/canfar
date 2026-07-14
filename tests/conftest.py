"""Shared pytest fixtures for deterministic CANFAR tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

ISOLATED_HOME = Path(
    os.environ.get(
        "CANFAR_TEST_HOME",
        str(Path(tempfile.gettempdir()) / "canfar-empty-home"),
    )
)


def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """Isolate ``HOME`` so tests never consume developer configuration."""
    ISOLATED_HOME.mkdir(parents=True, exist_ok=True)
    os.environ["CANFAR_TEST_HOME"] = str(ISOLATED_HOME)
    os.environ["HOME"] = str(ISOLATED_HOME)


@pytest.fixture(autouse=True)
def isolate_canfar_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear CANFAR env overrides so tests do not depend on shell state."""
    for key in list(os.environ):
        if key.startswith("CANFAR_") and key != "CANFAR_TEST_HOME":
            monkeypatch.delenv(key, raising=False)
