"""Shared async-runner helper for CLI commands.

CLI command callbacks are synchronous but drive asynchronous Session work.
Each one defines a coroutine and hands it to :func:`run`, keeping the
``asyncio`` entry point in a single place.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Coroutine

T = TypeVar("T")


def run(coro: Coroutine[object, object, T]) -> T:
    """Run a coroutine to completion from a synchronous CLI command.

    Args:
        coro: The coroutine to execute.

    Returns:
        The value returned by the coroutine.
    """
    return asyncio.run(coro)
