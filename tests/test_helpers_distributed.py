"""Contract tests for the public distributed helpers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Iterator

import pytest

from canfar.helpers import distributed

Partitioner = Callable[[Iterable[int], int, int], Iterator[int]]
DefaultPartitioner = Callable[[Iterable[int]], Iterator[int]]


def _partitions(
    partitioner: Partitioner,
    items: list[int],
    total: int,
) -> list[list[int]]:
    """Materialize every replica partition for one helper."""
    return [list(partitioner(items, replica, total)) for replica in range(1, total + 1)]


@pytest.mark.parametrize(
    ("partitioner", "items", "replica", "total", "expected"),
    [
        pytest.param(
            distributed.stripe,
            range(10),
            1,
            3,
            [0, 3, 6, 9],
            id="stripe-first",
        ),
        pytest.param(
            distributed.stripe,
            range(10),
            2,
            3,
            [1, 4, 7],
            id="stripe-second",
        ),
        pytest.param(
            distributed.stripe,
            range(100),
            1,
            10,
            list(range(0, 100, 10)),
            id="stripe-ten-replicas",
        ),
        pytest.param(
            distributed.chunk,
            range(12),
            1,
            3,
            [0, 1, 2, 3],
            id="chunk-first",
        ),
        pytest.param(
            distributed.chunk,
            range(10),
            4,
            4,
            [6, 7, 8, 9],
            id="chunk-remainder",
        ),
        pytest.param(
            distributed.chunk,
            [1, 2, 3],
            2,
            5,
            [2],
            id="chunk-sparse",
        ),
    ],
)
def test_documented_examples(
    partitioner: Partitioner,
    items: Iterable[int],
    replica: int,
    total: int,
    expected: list[int],
) -> None:
    """Keep the examples in the public API documentation executable."""
    assert list(partitioner(items, replica, total)) == expected


@pytest.mark.parametrize(
    ("items", "total", "expected_chunks", "expected_stripes"),
    [
        pytest.param([], 3, [[], [], []], [[], [], []], id="empty"),
        pytest.param(
            [0, 1, 2],
            5,
            [[0], [1], [2], [], []],
            [[0], [1], [2], [], []],
            id="sparse",
        ),
        pytest.param(
            list(range(8)),
            4,
            [[0, 1], [2, 3], [4, 5], [6, 7]],
            [[0, 4], [1, 5], [2, 6], [3, 7]],
            id="even",
        ),
        pytest.param(
            list(range(10)),
            4,
            [[0, 1], [2, 3], [4, 5], [6, 7, 8, 9]],
            [[0, 4, 8], [1, 5, 9], [2, 6], [3, 7]],
            id="uneven",
        ),
    ],
)
def test_partition_shapes_and_invariants(
    items: list[int],
    total: int,
    expected_chunks: list[list[int]],
    expected_stripes: list[list[int]],
) -> None:
    """Partition deterministically without losing or duplicating input."""
    chunks = _partitions(distributed.chunk, items, total)
    stripes = _partitions(distributed.stripe, items, total)

    assert chunks == expected_chunks
    assert stripes == expected_stripes
    assert [item for part in chunks for item in part] == items
    assert Counter(item for part in stripes for item in part) == Counter(items)


@pytest.mark.parametrize(
    ("partitioner", "expected"),
    [
        pytest.param(distributed.chunk, [3, 4, 5], id="chunk"),
        pytest.param(distributed.stripe, [1, 4, 7], id="stripe"),
    ],
)
def test_reads_current_environment_defaults(
    monkeypatch: pytest.MonkeyPatch,
    partitioner: DefaultPartitioner,
    expected: list[int],
) -> None:
    """Use the current container replica settings when arguments are omitted."""
    monkeypatch.setenv("REPLICA_ID", "2")
    monkeypatch.setenv("REPLICA_COUNT", "3")

    assert list(partitioner(range(10))) == expected


@pytest.mark.parametrize("partitioner", [distributed.chunk, distributed.stripe])
def test_missing_environment_defaults_to_one_replica(
    monkeypatch: pytest.MonkeyPatch,
    partitioner: DefaultPartitioner,
) -> None:
    """Use one replica when container settings are absent."""
    monkeypatch.delenv("REPLICA_ID", raising=False)
    monkeypatch.delenv("REPLICA_COUNT", raising=False)

    assert list(partitioner(range(5))) == list(range(5))


@pytest.mark.parametrize("partitioner", [distributed.chunk, distributed.stripe])
def test_explicit_arguments_override_environment(
    monkeypatch: pytest.MonkeyPatch,
    partitioner: Partitioner,
) -> None:
    """Ignore container settings when both arguments are explicit."""
    monkeypatch.setenv("REPLICA_ID", "not-an-integer")
    monkeypatch.setenv("REPLICA_COUNT", "not-an-integer")

    assert list(partitioner(range(6), 2, 3))


@pytest.mark.parametrize(
    ("partitioner", "expected"),
    [
        pytest.param(distributed.chunk, [2, 3], id="chunk"),
        pytest.param(distributed.stripe, [1, 4], id="stripe"),
    ],
)
def test_accepts_single_pass_iterables(
    partitioner: Partitioner,
    expected: list[int],
) -> None:
    """Accept iterators without reading them more than once."""
    items = (item for item in range(6))

    assert list(partitioner(items, 2, 3)) == expected


@pytest.mark.parametrize(
    ("replica", "total", "message"),
    [
        (1, 0, "total must be positive"),
        (1, -1, "total must be positive"),
        (0, 3, "replica must be >= 1"),
        (4, 3, "replica cannot exceed total"),
    ],
)
def test_chunk_rejects_invalid_replica_settings(
    replica: int,
    total: int,
    message: str,
) -> None:
    """Reject invalid chunk replica settings with stable messages."""
    with pytest.raises(ValueError, match=message):
        list(distributed.chunk(range(3), replica, total))


@pytest.mark.parametrize("replica", [0, -1, 4])
def test_stripe_returns_empty_for_out_of_range_replicas(replica: int) -> None:
    """Keep the legacy empty result for an out-of-range stripe replica."""
    assert list(distributed.stripe(range(3), replica, 3)) == []


@pytest.mark.parametrize("total", [0, -1])
def test_stripe_rejects_non_positive_total(total: int) -> None:
    """Reject a non-positive stripe replica count."""
    with pytest.raises(ValueError, match="positive integer"):
        list(distributed.stripe(range(3), 1, total))
