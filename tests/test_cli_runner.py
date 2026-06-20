"""Tests for the shared CLI async-runner helper."""

from __future__ import annotations

import pytest

from canfar.cli._run import run


def test_run_executes_coroutine_and_returns_result() -> None:
    """The runner drives a coroutine to completion and returns its value."""

    async def _coro() -> str:
        """Return a sentinel value."""
        return "done"

    assert run(_coro()) == "done"


def test_run_propagates_coroutine_exception() -> None:
    """Exceptions raised inside the coroutine surface to the caller."""

    async def _coro() -> None:
        """Raise to exercise exception propagation."""
        message = "boom"
        raise RuntimeError(message)

    with pytest.raises(RuntimeError, match="boom"):
        run(_coro())
