"""Shared pytest fixtures for deterministic CANFAR tests."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_canfar_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear CANFAR env overrides so tests do not depend on shell state."""
    for key in list(os.environ):
        if key.startswith("CANFAR_"):
            monkeypatch.delenv(key, raising=False)
