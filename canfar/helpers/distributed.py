"""Helper functions for distributed computing."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

T = TypeVar("T")


def stripe(
    iterable: Iterable[T],
    replica: int = int(os.environ.get("REPLICA_ID", "1")),
    total: int = int(os.environ.get("REPLICA_COUNT", "1")),
) -> Iterator[T]:
    """Returns every `total`-th item from the iterable with a `replica`-th offset.

    Args:
        iterable (Iterable[T]): The iterable to partition.
        replica (int, optional): The replica number.
            Defaults to int(os.environ.get("REPLICA_ID", 1)).
        total (int, optional): The total number of replicas.
            Defaults to int(os.environ.get("REPLICA_COUNT", 1)).

    Examples:
        >>> from canfar.helpers import distributed
        >>> dataset = range(100)
        >>> for data in distributed.partition(dataset, 1, 10):
                print(data)
        0, 10, 20, 30, 40, 50, 60, 70, 80, 90

    Yields:
        Iterator[T]: The `replica`-th partition of the iterable.
    """
    offset = replica - 1
    for index, item in enumerate(iterable):
        if index % total == offset:
            yield item


def chunk(
    iterable: Iterable[T],
    replica: int = int(os.environ.get("REPLICA_ID", "1")),
    total: int = int(os.environ.get("REPLICA_COUNT", "1")),
) -> Iterator[T]:
    """Returns the `replica`-th chunk of the iterable split into `total` chunks.

    This function distributes items from an iterable across multiple replicas canfar
    provided container environment variables.

    **Distribution Behavior:**

    - **Standard Distribution** (items >= replicas): Items are divided into roughly
      equal chunks, with the last replica receiving any remainder items.
    - **Sparse Distribution** (items < replicas): Each of the first N replicas gets
      exactly one item (where N = number of items), remaining replicas get empty
      results.

    Args:
        iterable (Iterable[T]): The iterable to distribute across replicas.
        replica (int, optional): The replica number using 1-based indexing.
            Must be >= 1 and <= total. Defaults to REPLICA_ID environment variable.
        total (int, optional): The total number of replicas. Must be > 0.
            Defaults to REPLICA_COUNT environment variable.

    Returns:
        Iterator[T]: An iterator yielding items assigned to this replica.

    Raises:
        ValueError: If replica < 1 (1-based indexing expected).
        ValueError: If replica > total (replica cannot exceed total replicas).
        ValueError: If total <= 0 (must have at least one replica).

    Note:
        This function is designed for use in canfar containerized environments where
        REPLICA_ID and REPLICA_COUNT environment variables are automatically set.
        The 1-based indexing matches the container environment expectations.

        For optimal performance with large datasets, consider using this function
        with iterators rather than converting large datasets to lists beforehand.

        When items < replicas, the sparse distribution ensures no replica receives
        an unfair share - each item goes to exactly one replica, and excess replicas
        receive empty results rather than duplicating data.
    """
    # Input validation
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

    # Convert 1-based replica to 0-based for internal calculations
    zero_based_replica = replica - 1

    # Check for sparse distribution case (more replicas than items)
    if count < total:
        # Sparse distribution: each of first 'count' replicas gets one item
        if zero_based_replica < count:
            yield items[zero_based_replica]
        # Remaining replicas get nothing (empty iterator)
        return

    # Standard distribution for normal cases (count >= total)
    # integer chunk size (floor)
    size = count // total
    # start/end of this chunk using zero-based replica
    start = zero_based_replica * size
    # last replica picks up any remainder
    end = (zero_based_replica + 1) * size if zero_based_replica < total - 1 else count
    yield from items[start:end]
