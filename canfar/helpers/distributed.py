"""Helper functions for distributed computing."""

from __future__ import annotations

import itertools
import os
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

T = TypeVar("T")


def stripe(
    iterable: Iterable[T],
    replica: int | None = None,
    total: int | None = None,
) -> Iterator[T]:
    """Return every ``total``-th item from ``iterable`` with a ``replica`` offset.

    Uses 1-based ``replica`` indexing to match ``REPLICA_ID`` in CANFAR
    containers. Replica 1 receives indices 0, ``total``, 2 * ``total``, …;
    replica 2 receives indices 1, ``total`` + 1, …; and so on.

    Unlike ``chunk``, ``stripe`` does not validate ``replica`` or ``total``.
    When ``replica`` is less than 1, or greater than ``total``, the result is
    empty. When ``total`` is zero, ``ValueError`` is raised.

    Args:
        iterable: The iterable to stripe across replicas.
        replica: The replica number (1-based). Defaults to ``REPLICA_ID``.
        total: The total number of replicas. Defaults to ``REPLICA_COUNT``.

    Yields:
        Items assigned to this replica.

    Examples:
        >>> from canfar.helpers import distributed
        >>> list(distributed.stripe(range(10), replica=1, total=3))
        [0, 3, 6, 9]
        >>> list(distributed.stripe(range(10), replica=2, total=3))
        [1, 4, 7]
        >>> list(distributed.stripe(range(100), replica=1, total=10))
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
    """
    replica = int(os.environ.get("REPLICA_ID", "1")) if replica is None else replica
    total = int(os.environ.get("REPLICA_COUNT", "1")) if total is None else total

    if replica < 1:
        return
    if total <= 0:
        yield from itertools.islice(iterable, replica - 1, None, total)
    elif replica > total:
        return
    else:
        yield from itertools.islice(iterable, replica - 1, None, total)


def chunk(
    iterable: Iterable[T],
    replica: int | None = None,
    total: int | None = None,
) -> Iterator[T]:
    """Return the ``replica``-th contiguous chunk of ``iterable``.

    Splits ``iterable`` into ``total`` roughly equal contiguous chunks using
    1-based ``replica`` indexing to match ``REPLICA_ID`` in CANFAR containers.

    **Distribution behavior:**

    - **Standard** (``len(items) >= total``): Items are divided into equal-sized
      chunks; the last replica receives any remainder.
    - **Sparse** (``len(items) < total``): Each of the first ``len(items)``
      replicas receives exactly one item; remaining replicas get nothing.

    Args:
        iterable: The iterable to distribute across replicas.
        replica: The replica number (1-based). Must be >= 1 and <= ``total``.
            Defaults to ``REPLICA_ID``.
        total: The total number of replicas. Must be > 0. Defaults to
            ``REPLICA_COUNT``.

    Yields:
        Items assigned to this replica.

    Raises:
        ValueError: If ``replica`` < 1, ``replica`` > ``total``, or ``total`` <= 0.

    Examples:
        >>> from canfar.helpers import distributed
        >>> list(distributed.chunk(range(12), replica=1, total=3))
        [0, 1, 2, 3]
        >>> list(distributed.chunk(range(10), replica=4, total=4))
        [6, 7, 8, 9]
        >>> list(distributed.chunk([1, 2, 3], replica=2, total=5))
        [2]
    """
    replica = int(os.environ.get("REPLICA_ID", "1")) if replica is None else replica
    total = int(os.environ.get("REPLICA_COUNT", "1")) if total is None else total

    if total <= 0:
        msg = "total must be positive"
        raise ValueError(msg)
    if replica < 1:
        msg = "replica must be >= 1 (1-based indexing expected)"
        raise ValueError(msg)
    if replica > total:
        msg = "replica cannot exceed total"
        raise ValueError(msg)

    items = list(iterable)
    count = len(items)
    zero_based_replica = replica - 1

    if count < total:
        if zero_based_replica < count:
            yield items[zero_based_replica]
        return

    size = count // total
    start = zero_based_replica * size
    end = (zero_based_replica + 1) * size if zero_based_replica < total - 1 else count
    yield from items[start:end]
