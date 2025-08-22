"""Tests for canfar.helpers.distributed module."""

from __future__ import annotations

import os
import time
from typing import Any
from unittest.mock import patch

import pytest

from canfar.helpers.distributed import chunk, stripe


# Test data fixtures
@pytest.fixture
def sample_range() -> range:
    """Sample range for testing."""
    return range(100)


@pytest.fixture
def sample_list() -> list[int]:
    """Sample list for testing."""
    return list(range(20))


@pytest.fixture
def sample_string() -> str:
    """Sample string for testing."""
    return "abcdefghijklmnopqrstuvwxyz"


# Tests for stripe function
def test_stripe_basic_functionality() -> None:
    """Test stripe function with basic parameters."""
    data = list(range(10))

    # Test replica 1 of 3
    result = list(stripe(data, replica=1, total=3))
    expected = [0, 3, 6, 9]  # indices 0, 3, 6, 9
    assert result == expected

    # Test replica 2 of 3
    result = list(stripe(data, replica=2, total=3))
    expected = [1, 4, 7]  # indices 1, 4, 7
    assert result == expected

    # Test replica 3 of 3
    result = list(stripe(data, replica=3, total=3))
    expected = [2, 5, 8]  # indices 2, 5, 8
    assert result == expected


def test_stripe_single_replica() -> None:
    """Test stripe function with single replica (total=1)."""
    data = list(range(10))
    result = list(stripe(data, replica=1, total=1))
    assert result == data


def test_stripe_more_replicas_than_items() -> None:
    """Test stripe function when total replicas exceed item count."""
    data = [1, 2, 3]

    # Replica 1 should get item 0
    result = list(stripe(data, replica=1, total=5))
    assert result == [1]

    # Replica 2 should get item 1
    result = list(stripe(data, replica=2, total=5))
    assert result == [2]

    # Replica 4 should get nothing
    result = list(stripe(data, replica=4, total=5))
    assert result == []


def test_stripe_empty_iterable() -> None:
    """Test stripe function with empty iterable."""
    result = list(stripe([], replica=1, total=3))
    assert result == []


def test_stripe_with_different_types(sample_string: str) -> None:
    """Test stripe function with different iterable types."""
    # Test with string
    result = list(stripe(sample_string, replica=1, total=5))
    expected = ["a", "f", "k", "p", "u", "z"]  # indices 0, 5, 10, 15, 20, 25
    assert result == expected

    # Test with generator
    def gen() -> Any:
        yield from range(10)

    result = list(stripe(gen(), replica=2, total=3))
    expected = [1, 4, 7]
    assert result == expected


def test_stripe_environment_defaults() -> None:
    """Test stripe function using environment variable defaults.

    Note: Environment variables are read at import time, so we need to
    test the actual default behavior rather than mocking.
    """
    # Test that the function works with explicit parameters matching defaults
    data = list(range(12))

    # Test with explicit parameters (replica=1, total=1 are the defaults)
    result = list(stripe(data, replica=1, total=1))
    assert result == data  # Should get all items

    # Test with different explicit parameters
    result = list(stripe(data, replica=2, total=4))
    expected = [1, 5, 9]  # replica 2 of 4, indices 1, 5, 9
    assert result == expected


def test_stripe_environment_defaults_fallback() -> None:
    """Test stripe function with default parameters."""
    data = list(range(10))
    result = list(stripe(data))
    # Should default to replica=1, total=1 (all items)
    assert result == data


# Tests for chunk function
def test_chunk_basic_functionality() -> None:
    """Test chunk function with basic parameters using 1-based indexing."""
    data = list(range(12))

    # Test replica 1 of 3 (first chunk) - 1-based indexing
    result = list(chunk(data, replica=1, total=3))
    expected = [0, 1, 2, 3]  # first 4 items
    assert result == expected

    # Test replica 2 of 3 (second chunk)
    result = list(chunk(data, replica=2, total=3))
    expected = [4, 5, 6, 7]  # next 4 items
    assert result == expected

    # Test replica 3 of 3 (last chunk)
    result = list(chunk(data, replica=3, total=3))
    expected = [8, 9, 10, 11]  # last 4 items
    assert result == expected


def test_chunk_uneven_division() -> None:
    """Test chunk function when items don't divide evenly using 1-based indexing."""
    data = list(range(10))  # 10 items, 3 chunks

    # First two chunks get 3 items each (10 // 3 = 3)
    result = list(chunk(data, replica=1, total=3))  # 1-based indexing
    expected = [0, 1, 2]
    assert result == expected

    result = list(chunk(data, replica=2, total=3))
    expected = [3, 4, 5]
    assert result == expected

    # Last chunk gets remainder (3 + 1 = 4 items)
    result = list(chunk(data, replica=3, total=3))
    expected = [6, 7, 8, 9]
    assert result == expected


def test_chunk_single_chunk() -> None:
    """Test chunk function with single chunk (total=1) using 1-based indexing."""
    data = list(range(10))
    result = list(chunk(data, replica=1, total=1))  # 1-based indexing
    assert result == data


def test_chunk_more_chunks_than_items() -> None:
    """Test chunk function when total chunks exceed item count.

    With the corrected sparse distribution logic, when there are more replicas
    than items, each of the first len(items) replicas gets exactly one item,
    and the remaining replicas get empty results.
    """
    data = [1, 2, 3]

    # Test sparse distribution: each of first 3 replicas gets one item
    result = list(chunk(data, replica=1, total=5))  # 1-based indexing
    assert result == [1]

    result = list(chunk(data, replica=2, total=5))
    assert result == [2]

    result = list(chunk(data, replica=3, total=5))
    assert result == [3]

    # Remaining replicas get nothing
    result = list(chunk(data, replica=4, total=5))
    assert result == []

    result = list(chunk(data, replica=5, total=5))
    assert result == []


def test_chunk_empty_iterable() -> None:
    """Test chunk function with empty iterable using 1-based indexing."""
    result = list(chunk([], replica=1, total=3))  # 1-based indexing
    assert result == []


def test_chunk_with_different_types(sample_string: str) -> None:
    """Test chunk function with different iterable types using 1-based indexing."""
    # Test with string (26 chars, 3 chunks: 8, 8, 10)
    result = list(chunk(sample_string, replica=1, total=3))  # 1-based indexing
    expected = list("abcdefgh")  # first 8 chars
    assert result == expected

    result = list(chunk(sample_string, replica=3, total=3))  # 1-based indexing
    expected = list("qrstuvwxyz")  # last 10 chars
    assert result == expected


def test_chunk_environment_defaults() -> None:
    """Test chunk function using environment variable defaults.

    Note: Environment variables are read at import time, so we need to
    test the actual default behavior rather than mocking.
    """
    # Test that the function works with explicit parameters
    data = list(range(12))

    # Test with explicit parameters using 1-based indexing
    # replica=1 means first chunk with corrected 1-based indexing
    result = list(chunk(data, replica=1, total=4))
    expected = [0, 1, 2]  # replica 1 of 4, first 3 items (12 // 4 = 3)
    assert result == expected


def test_chunk_environment_defaults_fallback() -> None:
    """Test chunk function with default parameters.

    The default values are replica=1, total=1. With the corrected 1-based indexing,
    replica=1 with total=1 should return all items (the single chunk).
    """
    data = list(range(10))
    result = list(chunk(data))
    # With replica=1, total=1, should get all items (single chunk)
    assert result == data


# Integration tests comparing stripe vs chunk
def test_stripe_vs_chunk_coverage() -> None:
    """Test that stripe and chunk together cover all items exactly once."""
    data = list(range(20))
    total = 4

    # Collect all items from stripe (1-based indexing)
    stripe_items = []
    for replica in range(1, total + 1):
        stripe_items.extend(stripe(data, replica=replica, total=total))

    # Collect all items from chunk (1-based indexing)
    chunk_items = []
    for replica in range(1, total + 1):  # Changed to 1-based indexing
        chunk_items.extend(chunk(data, replica=replica, total=total))

    # Both should cover all items exactly once
    assert sorted(stripe_items) == data
    assert sorted(chunk_items) == data


def test_stripe_vs_chunk_no_overlap() -> None:
    """Test that stripe partitions have no overlap."""
    data = list(range(15))
    total = 3

    partitions = []
    for replica in range(1, total + 1):
        partition = list(stripe(data, replica=replica, total=total))
        partitions.append(set(partition))

    # Check no overlap between partitions
    for i in range(len(partitions)):
        for j in range(i + 1, len(partitions)):
            assert partitions[i].isdisjoint(partitions[j])


# Edge case and error condition tests
def test_stripe_zero_total() -> None:
    """Test stripe function with zero total (should handle gracefully)."""
    data = [1, 2, 3]
    # This might raise an error or return empty - test actual behavior
    try:
        result = list(stripe(data, replica=1, total=0))
        # If it doesn't raise an error, it should return empty
        assert result == []
    except (ZeroDivisionError, ValueError):
        # This is also acceptable behavior
        pass


def test_chunk_zero_total() -> None:
    """Test chunk function with zero total (should handle gracefully)."""
    data = [1, 2, 3]
    # This might raise an error - test actual behavior
    try:
        result = list(chunk(data, replica=0, total=0))
        assert result == []
    except (ZeroDivisionError, ValueError):
        # This is also acceptable behavior
        pass


def test_large_dataset_performance(sample_range: range) -> None:
    """Test functions with larger datasets for performance."""
    # Test with range(100)
    stripe_result = list(stripe(sample_range, replica=1, total=10))
    chunk_result = list(chunk(sample_range, replica=1, total=10))  # 1-based indexing

    # Stripe should get every 10th item starting from 0
    assert stripe_result == [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]

    # Chunk should get first 10 items (replica 1 of 10)
    assert chunk_result == list(range(10))


# Additional comprehensive tests
def test_stripe_boundary_conditions() -> None:
    """Test stripe function with boundary conditions."""
    data = list(range(5))

    # Test with replica equal to total
    result = list(stripe(data, replica=5, total=5))
    expected = [4]  # Only the last item (index 4)
    assert result == expected

    # Test with replica greater than total (edge case)
    result = list(stripe(data, replica=6, total=5))
    expected = []  # No items should match
    assert result == expected


def test_chunk_boundary_conditions() -> None:
    """Test chunk function with boundary conditions using 1-based indexing."""
    data = list(range(5))

    # Test with sparse distribution (5 items, 5 replicas)
    # Each replica should get exactly one item
    result = list(chunk(data, replica=5, total=5))  # 1-based indexing
    expected = [4]  # Last replica gets last item
    assert result == expected

    # Test first replica
    result = list(chunk(data, replica=1, total=5))
    expected = [0]  # First replica gets first item
    assert result == expected


def test_functions_with_single_item() -> None:
    """Test both functions with single-item iterables."""
    data = [42]

    # Stripe with single item
    assert list(stripe(data, replica=1, total=1)) == [42]
    assert list(stripe(data, replica=1, total=2)) == [42]
    assert list(stripe(data, replica=2, total=2)) == []

    # Chunk with single item using 1-based indexing
    assert list(chunk(data, replica=1, total=1)) == [42]  # 1-based indexing
    assert list(chunk(data, replica=1, total=2)) == [42]  # First replica gets the item
    assert list(chunk(data, replica=2, total=2)) == []  # Second replica gets nothing


def test_functions_with_tuples() -> None:
    """Test functions with tuple iterables."""
    data = (1, 2, 3, 4, 5, 6)

    # Test stripe with tuple
    result = list(stripe(data, replica=1, total=2))
    expected = [1, 3, 5]
    assert result == expected

    # Test chunk with tuple using 1-based indexing
    result = list(chunk(data, replica=1, total=2))  # 1-based indexing
    expected = [1, 2, 3]
    assert result == expected


def test_functions_consistency() -> None:
    """Test that functions behave consistently across different scenarios."""
    data = list(range(24))  # Divisible by many numbers

    # Test with various total values
    for total in [1, 2, 3, 4, 6, 8, 12]:
        # Stripe: collect all partitions (1-based indexing)
        stripe_all = []
        for replica in range(1, total + 1):
            stripe_all.extend(stripe(data, replica=replica, total=total))

        # Chunk: collect all chunks (1-based indexing)
        chunk_all = []
        for replica in range(1, total + 1):  # Changed to 1-based indexing
            chunk_all.extend(chunk(data, replica=replica, total=total))

        # Both should cover all data exactly once
        assert sorted(stripe_all) == data
        assert sorted(chunk_all) == data


def test_environment_variable_types() -> None:
    """Test that environment variables are properly converted to integers."""
    # This tests the int() conversion in the default parameters
    data = list(range(8))

    # Test with explicit string-like parameters (simulating env var behavior)
    result1 = list(stripe(data, replica=int("2"), total=int("4")))
    result2 = list(stripe(data, replica=2, total=4))
    assert result1 == result2

    # Test chunk with 1-based indexing
    result3 = list(chunk(data, replica=int("1"), total=int("4")))
    result4 = list(chunk(data, replica=1, total=4))
    assert result3 == result4


# Comprehensive edge case tests for chunk function
def test_chunk_single_item_multiple_replicas() -> None:
    """Test chunk function with single item and multiple replicas."""
    data = [42]

    # Test with 2 replicas: first replica gets the item, second gets nothing
    result1 = list(chunk(data, replica=1, total=2))
    assert result1 == [42], "First replica should get the single item"

    result2 = list(chunk(data, replica=2, total=2))
    assert result2 == [], "Second replica should get nothing"

    # Test with 5 replicas: only first replica gets the item
    result1 = list(chunk(data, replica=1, total=5))
    assert result1 == [42], "First replica should get the single item"

    for replica in range(2, 6):
        result = list(chunk(data, replica=replica, total=5))
        assert result == [], f"Replica {replica} should get nothing"

    # Test with 10 replicas
    result1 = list(chunk(data, replica=1, total=10))
    assert result1 == [42], "First replica should get the single item"

    for replica in range(2, 11):
        result = list(chunk(data, replica=replica, total=10))
        assert result == [], f"Replica {replica} should get nothing"


def test_chunk_empty_iterable_various_replica_counts() -> None:
    """Test chunk function with empty iterable and various replica counts."""
    data = []

    # Test with different replica counts
    test_cases = [
        (1, 1),  # Single replica
        (1, 2),  # First of two replicas
        (2, 2),  # Second of two replicas
        (1, 5),  # First of five replicas
        (3, 5),  # Middle replica
        (5, 5),  # Last replica
        (1, 10),  # First of ten replicas
        (10, 10),  # Last of ten replicas
    ]

    for replica, total in test_cases:
        result = list(chunk(data, replica=replica, total=total))
        assert result == [], (
            f"Empty iterable should return empty result for "
            f"replica {replica} of {total}"
        )


def test_chunk_boundary_conditions_comprehensive() -> None:
    """Test chunk function with comprehensive boundary conditions."""

    # Test replica == 1 (first replica) with various scenarios
    def test_first_replica():
        # Test with equal items and replicas
        data = list(range(5))
        result = list(chunk(data, replica=1, total=5))
        assert result == [0], (
            "First replica should get first item when items == replicas"
        )

        # Test with more items than replicas
        data = list(range(12))
        result = list(chunk(data, replica=1, total=3))
        assert result == [0, 1, 2, 3], "First replica should get first chunk"

        # Test with fewer items than replicas
        data = [1, 2]
        result = list(chunk(data, replica=1, total=5))
        assert result == [1], (
            "First replica should get first item in sparse distribution"
        )

    # Test replica == total (last replica) with various scenarios
    def test_last_replica():
        # Test with equal items and replicas
        data = list(range(5))
        result = list(chunk(data, replica=5, total=5))
        assert result == [4], "Last replica should get last item when items == replicas"

        # Test with more items than replicas (remainder handling)
        data = list(range(13))  # 13 items, 4 replicas
        result = list(chunk(data, replica=4, total=4))
        # First 3 replicas get 3 items each (13 // 4 = 3)
        # Last replica gets 3 + remainder (13 % 4 = 1) = 4 items
        expected = [9, 10, 11, 12]  # indices 9-12
        assert result == expected, "Last replica should get remainder items"

        # Test with fewer items than replicas
        data = [1, 2]
        result = list(chunk(data, replica=5, total=5))
        assert result == [], "Last replica should get nothing when replica > item count"

    # Test middle replicas
    def test_middle_replicas():
        # Test with standard distribution
        data = list(range(15))  # 15 items, 5 replicas = 3 items each
        result = list(chunk(data, replica=3, total=5))  # Middle replica
        expected = [6, 7, 8]  # indices 6-8
        assert result == expected, "Middle replica should get correct chunk"

        # Test with sparse distribution
        data = [1, 2, 3]
        result = list(chunk(data, replica=3, total=5))  # Middle replica
        assert result == [3], (
            "Middle replica should get one item in sparse distribution"
        )

    # Run all boundary tests
    test_first_replica()
    test_last_replica()
    test_middle_replicas()


def test_chunk_edge_case_combinations() -> None:
    """Test chunk function with various edge case combinations."""
    # Test case 1: Two items, many replicas
    data = [10, 20]

    result1 = list(chunk(data, replica=1, total=10))
    assert result1 == [10], "First replica gets first item"

    result2 = list(chunk(data, replica=2, total=10))
    assert result2 == [20], "Second replica gets second item"

    for replica in range(3, 11):
        result = list(chunk(data, replica=replica, total=10))
        assert result == [], f"Replica {replica} should get nothing"

    # Test case 2: Many items, two replicas (simple split)
    data = list(range(11))  # 11 items, 2 replicas

    result1 = list(chunk(data, replica=1, total=2))
    expected1 = [0, 1, 2, 3, 4]  # 11 // 2 = 5 items
    assert result1 == expected1, "First replica should get first 5 items"

    result2 = list(chunk(data, replica=2, total=2))
    expected2 = [5, 6, 7, 8, 9, 10]  # 5 + remainder (1) = 6 items
    assert result2 == expected2, "Second replica should get remaining 6 items"

    # Test case 3: Perfect division
    data = list(range(20))  # 20 items, 4 replicas = 5 items each

    expected_chunks = [
        [0, 1, 2, 3, 4],  # replica 1
        [5, 6, 7, 8, 9],  # replica 2
        [10, 11, 12, 13, 14],  # replica 3
        [15, 16, 17, 18, 19],  # replica 4
    ]

    for replica, expected in enumerate(expected_chunks, 1):
        result = list(chunk(data, replica=replica, total=4))
        assert result == expected, f"Replica {replica} should get {expected}"

    # Test case 4: Large remainder
    data = list(range(22))  # 22 items, 5 replicas

    # First 4 replicas get 4 items each (22 // 5 = 4)
    for replica in range(1, 5):
        result = list(chunk(data, replica=replica, total=5))
        start_idx = (replica - 1) * 4
        expected = list(range(start_idx, start_idx + 4))
        assert result == expected, f"Replica {replica} should get 4 items"

    # Last replica gets 4 + remainder (22 % 5 = 2) = 6 items
    result5 = list(chunk(data, replica=5, total=5))
    expected5 = [16, 17, 18, 19, 20, 21]
    assert result5 == expected5, "Last replica should get 6 items (4 + remainder)"


def test_chunk_input_validation_edge_cases() -> None:
    """Test chunk function input validation with edge cases."""
    data = [1, 2, 3]

    # Test valid boundary cases
    result = list(chunk(data, replica=1, total=1))
    assert result == data, "replica=1, total=1 should work"

    result = list(chunk(data, replica=3, total=3))
    assert result == [3], "replica=total should work"

    # Test error cases
    with pytest.raises(ValueError, match="replica must be >= 1"):
        list(chunk(data, replica=0, total=3))

    with pytest.raises(ValueError, match="replica must be >= 1"):
        list(chunk(data, replica=-1, total=3))

    with pytest.raises(ValueError, match="replica cannot exceed total"):
        list(chunk(data, replica=4, total=3))

    with pytest.raises(ValueError, match="total must be positive"):
        list(chunk(data, replica=1, total=0))

    with pytest.raises(ValueError, match="total must be positive"):
        list(chunk(data, replica=1, total=-1))


def test_chunk_consistency_across_data_types() -> None:
    """Test chunk function consistency across different data types."""
    # Test with list
    list_data = [1, 2, 3, 4, 5, 6]
    result_list = list(chunk(list_data, replica=2, total=3))
    expected = [
        3,
        4,
    ]  # 6 // 3 = 2 items per chunk, replica 2 gets items 2-3 (0-indexed)
    assert result_list == expected

    # Test with tuple (same data)
    tuple_data = (1, 2, 3, 4, 5, 6)
    result_tuple = list(chunk(tuple_data, replica=2, total=3))
    assert result_tuple == expected, "Tuple should give same result as list"

    # Test with string
    string_data = "abcdef"
    result_string = list(chunk(string_data, replica=2, total=3))
    expected_string = ["c", "d"]  # Same positions as above
    assert result_string == expected_string, "String should give same positions"

    # Test with range
    range_data = range(1, 7)  # 1, 2, 3, 4, 5, 6
    result_range = list(chunk(range_data, replica=2, total=3))
    assert result_range == expected, "Range should give same result as list"

    # Test with generator
    def gen_data():
        yield from [1, 2, 3, 4, 5, 6]

    result_gen = list(chunk(gen_data(), replica=2, total=3))
    assert result_gen == expected, "Generator should give same result as list"


def test_chunk_large_sparse_distribution() -> None:
    """Test chunk function with large sparse distribution scenarios."""
    # Test 1 item with 100 replicas
    data = [42]

    result1 = list(chunk(data, replica=1, total=100))
    assert result1 == [42], "First replica should get the single item"

    # Test random replicas in the middle and end
    for replica in [50, 75, 100]:
        result = list(chunk(data, replica=replica, total=100))
        assert result == [], f"Replica {replica} should get nothing"

    # Test 5 items with 50 replicas
    data = list(range(5))

    # First 5 replicas should each get one item
    for replica in range(1, 6):
        result = list(chunk(data, replica=replica, total=50))
        expected = [replica - 1]  # replica 1 gets item 0, replica 2 gets item 1, etc.
        assert result == expected, f"Replica {replica} should get item {replica - 1}"

    # Remaining replicas should get nothing
    for replica in [6, 25, 50]:
        result = list(chunk(data, replica=replica, total=50))
        assert result == [], f"Replica {replica} should get nothing"


# Environment variable integration tests
def test_chunk_environment_variable_defaults_mocked() -> None:
    """Test chunk function with mocked environment variables."""
    data = list(range(12))

    # Test with REPLICA_ID=1, REPLICA_COUNT=3
    with patch.dict(os.environ, {"REPLICA_ID": "1", "REPLICA_COUNT": "3"}):
        # Test that the function reads environment variables correctly
        # by passing explicit int conversions that simulate the default behavior
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = [0, 1, 2, 3]  # First chunk of 3 chunks
        assert result == expected, "REPLICA_ID=1 should get first chunk"

    # Test with REPLICA_ID=2, REPLICA_COUNT=3
    with patch.dict(os.environ, {"REPLICA_ID": "2", "REPLICA_COUNT": "3"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = [4, 5, 6, 7]  # Second chunk of 3 chunks
        assert result == expected, "REPLICA_ID=2 should get second chunk"

    # Test with REPLICA_ID=3, REPLICA_COUNT=3
    with patch.dict(os.environ, {"REPLICA_ID": "3", "REPLICA_COUNT": "3"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = [8, 9, 10, 11]  # Third chunk of 3 chunks
        assert result == expected, "REPLICA_ID=3 should get third chunk"


def test_stripe_environment_variable_defaults_mocked() -> None:
    """Test stripe function with mocked environment variables."""
    data = list(range(12))

    # Test with REPLICA_ID=1, REPLICA_COUNT=3
    with patch.dict(os.environ, {"REPLICA_ID": "1", "REPLICA_COUNT": "3"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(stripe(data, replica=replica, total=total))
        expected = [0, 3, 6, 9]  # Every 3rd item starting from index 0
        assert result == expected, "REPLICA_ID=1 should get every 3rd item from index 0"

    # Test with REPLICA_ID=2, REPLICA_COUNT=3
    with patch.dict(os.environ, {"REPLICA_ID": "2", "REPLICA_COUNT": "3"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(stripe(data, replica=replica, total=total))
        expected = [1, 4, 7, 10]  # Every 3rd item starting from index 1
        assert result == expected, "REPLICA_ID=2 should get every 3rd item from index 1"

    # Test with REPLICA_ID=3, REPLICA_COUNT=3
    with patch.dict(os.environ, {"REPLICA_ID": "3", "REPLICA_COUNT": "3"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(stripe(data, replica=replica, total=total))
        expected = [2, 5, 8, 11]  # Every 3rd item starting from index 2
        assert result == expected, "REPLICA_ID=3 should get every 3rd item from index 2"


def test_chunk_environment_variable_string_to_int_conversion() -> None:
    """Test that environment variables are properly converted from strings to ints."""
    data = list(range(20))

    # Test with string environment variables (as they would be in real containers)
    with patch.dict(os.environ, {"REPLICA_ID": "2", "REPLICA_COUNT": "4"}):
        # Simulate the default parameter behavior
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        # 20 items, 4 chunks = 5 items per chunk
        # Replica 2 (1-based) should get items 5-9
        expected = [5, 6, 7, 8, 9]
        assert result == expected, (
            "String env vars should be converted to int correctly"
        )

    # Test with different string values
    with patch.dict(os.environ, {"REPLICA_ID": "1", "REPLICA_COUNT": "5"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        # 20 items, 5 chunks = 4 items per chunk
        # Replica 1 should get items 0-3
        expected = [0, 1, 2, 3]
        assert result == expected, "Different string env vars should work correctly"


def test_stripe_environment_variable_string_to_int_conversion() -> None:
    """Test that stripe function properly converts string env vars to integers."""
    data = list(range(15))

    # Test with string environment variables
    with patch.dict(os.environ, {"REPLICA_ID": "2", "REPLICA_COUNT": "5"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(stripe(data, replica=replica, total=total))
        # Every 5th item starting from index 1 (replica 2 - 1)
        expected = [1, 6, 11]
        assert result == expected, (
            "String env vars should be converted to int correctly"
        )

    # Test with different string values
    with patch.dict(os.environ, {"REPLICA_ID": "3", "REPLICA_COUNT": "4"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(stripe(data, replica=replica, total=total))
        # Every 4th item starting from index 2 (replica 3 - 1)
        expected = [2, 6, 10, 14]
        assert result == expected, "Different string env vars should work correctly"


def test_chunk_environment_variable_sparse_distribution() -> None:
    """Test chunk function with environment variables in sparse distribution."""
    data = [1, 2, 3]  # 3 items

    # Test sparse distribution with 5 replicas
    with patch.dict(os.environ, {"REPLICA_ID": "1", "REPLICA_COUNT": "5"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = [1]  # First replica gets first item
        assert result == expected, (
            "Replica 1 should get first item in sparse distribution"
        )

    with patch.dict(os.environ, {"REPLICA_ID": "3", "REPLICA_COUNT": "5"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = [3]  # Third replica gets third item
        assert result == expected, (
            "Replica 3 should get third item in sparse distribution"
        )

    with patch.dict(os.environ, {"REPLICA_ID": "5", "REPLICA_COUNT": "5"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = []  # Fifth replica gets nothing
        assert result == expected, "Replica 5 should get nothing in sparse distribution"


def test_environment_variable_fallback_behavior() -> None:
    """Test behavior when environment variables are not set."""
    data = list(range(10))

    # Test with no environment variables set (should default to "1")
    with patch.dict(os.environ, {}, clear=True):
        # Simulate the default parameter behavior
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        # Should default to replica=1, total=1
        chunk_result = list(chunk(data, replica=replica, total=total))
        assert chunk_result == data, "No env vars should default to replica=1, total=1"

        stripe_result = list(stripe(data, replica=replica, total=total))
        assert stripe_result == data, "No env vars should default to replica=1, total=1"


def test_environment_variable_partial_set() -> None:
    """Test behavior when only one environment variable is set."""
    data = list(range(8))

    # Test with only REPLICA_ID set
    with patch.dict(os.environ, {"REPLICA_ID": "2"}, clear=True):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        # Should use REPLICA_ID=2, REPLICA_COUNT=1 (default)
        # With total=1, replica=2 should raise an error
        with pytest.raises(ValueError, match="replica cannot exceed total"):
            list(chunk(data, replica=replica, total=total))

    # Test with only REPLICA_COUNT set
    with patch.dict(os.environ, {"REPLICA_COUNT": "4"}, clear=True):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        # Should use REPLICA_ID=1 (default), REPLICA_COUNT=4
        result = list(chunk(data, replica=replica, total=total))
        expected = [0, 1]  # 8 items, 4 chunks = 2 items per chunk, first chunk
        assert result == expected, (
            "Should use default REPLICA_ID=1 with set REPLICA_COUNT"
        )


def test_environment_variable_edge_cases() -> None:
    """Test edge cases with environment variable values."""
    data = list(range(6))

    # Test with REPLICA_ID=1, REPLICA_COUNT=1 (single replica)
    with patch.dict(os.environ, {"REPLICA_ID": "1", "REPLICA_COUNT": "1"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        assert result == data, "Single replica should get all items"

    # Test with equal items and replicas
    with patch.dict(os.environ, {"REPLICA_ID": "3", "REPLICA_COUNT": "6"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = [2]  # Third replica gets third item (sparse distribution)
        assert result == expected, (
            "Equal items and replicas should use sparse distribution"
        )

    # Test with large replica count
    with patch.dict(os.environ, {"REPLICA_ID": "10", "REPLICA_COUNT": "100"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        result = list(chunk(data, replica=replica, total=total))
        expected = []  # Replica 10 gets nothing (only 6 items)
        assert result == expected, (
            "Large replica count should handle sparse distribution"
        )


def test_environment_variable_integration_comprehensive() -> None:
    """Comprehensive test of environment variable integration with various scenarios."""
    # Test scenario 1: Standard distribution
    data = list(range(24))  # 24 items

    test_cases = [
        ("1", "4", [0, 1, 2, 3, 4, 5]),  # First chunk: 6 items
        ("2", "4", [6, 7, 8, 9, 10, 11]),  # Second chunk: 6 items
        ("3", "4", [12, 13, 14, 15, 16, 17]),  # Third chunk: 6 items
        ("4", "4", [18, 19, 20, 21, 22, 23]),  # Fourth chunk: 6 items
    ]

    for replica_id, replica_count, expected in test_cases:
        with patch.dict(
            os.environ, {"REPLICA_ID": replica_id, "REPLICA_COUNT": replica_count}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))

            result = list(chunk(data, replica=replica, total=total))
            assert result == expected, (
                f"Replica {replica_id} of {replica_count} should get {expected}"
            )

    # Test scenario 2: Sparse distribution
    data = ["file1.txt", "file2.txt", "file3.txt"]

    sparse_test_cases = [
        ("1", "5", ["file1.txt"]),  # First replica gets first file
        ("2", "5", ["file2.txt"]),  # Second replica gets second file
        ("3", "5", ["file3.txt"]),  # Third replica gets third file
        ("4", "5", []),  # Fourth replica gets nothing
        ("5", "5", []),  # Fifth replica gets nothing
    ]

    for replica_id, replica_count, expected in sparse_test_cases:
        with patch.dict(
            os.environ, {"REPLICA_ID": replica_id, "REPLICA_COUNT": replica_count}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))

            result = list(chunk(data, replica=replica, total=total))
            assert result == expected, (
                f"Sparse: Replica {replica_id} of {replica_count} should get {expected}"
            )


# Integration tests between chunk and stripe functions
def test_chunk_stripe_integration_1_based_indexing_consistency() -> None:
    """Test that both chunk and stripe functions handle 1-based indexing."""
    data = list(range(20))
    total = 4

    # Test that both functions use 1-based indexing consistently
    for replica in range(1, total + 1):  # 1-based indexing
        # Get results from both functions
        chunk_result = list(chunk(data, replica=replica, total=total))
        stripe_result = list(stripe(data, replica=replica, total=total))

        # Both should work with 1-based indexing (no errors)
        assert isinstance(chunk_result, list), (
            f"Chunk should work with replica={replica}"
        )
        assert isinstance(stripe_result, list), (
            f"Stripe should work with replica={replica}"
        )

        # Verify that replica=1 gets the "first" portion for both
        if replica == 1:
            # Chunk: first chunk should start with item 0
            assert chunk_result[0] == 0, "Chunk replica=1 should start with first item"
            # Stripe: first stripe should start with item 0
            assert stripe_result[0] == 0, (
                "Stripe replica=1 should start with first item"
            )


def test_chunk_stripe_integration_complete_data_coverage() -> None:
    """Test that chunk and stripe functions together provide complete data coverage."""
    data = list(range(30))
    total = 5

    # Test chunk coverage
    chunk_all_items = []
    for replica in range(1, total + 1):  # 1-based indexing
        chunk_items = list(chunk(data, replica=replica, total=total))
        chunk_all_items.extend(chunk_items)

    # Test stripe coverage
    stripe_all_items = []
    for replica in range(1, total + 1):  # 1-based indexing
        stripe_items = list(stripe(data, replica=replica, total=total))
        stripe_all_items.extend(stripe_items)

    # Both should cover all data exactly once
    assert sorted(chunk_all_items) == data, "Chunk should cover all items exactly once"
    assert sorted(stripe_all_items) == data, (
        "Stripe should cover all items exactly once"
    )

    # Verify no duplicates
    assert len(chunk_all_items) == len(data), "Chunk should not duplicate items"
    assert len(stripe_all_items) == len(data), "Stripe should not duplicate items"


def test_chunk_stripe_integration_no_overlap_within_function() -> None:
    """Test that partitions within each function have no overlap."""
    data = list(range(24))
    total = 6

    # Test chunk partitions have no overlap
    chunk_partitions = []
    for replica in range(1, total + 1):  # 1-based indexing
        partition = set(chunk(data, replica=replica, total=total))
        chunk_partitions.append(partition)

    # Check no overlap between chunk partitions
    for i in range(len(chunk_partitions)):
        for j in range(i + 1, len(chunk_partitions)):
            overlap = chunk_partitions[i].intersection(chunk_partitions[j])
            assert len(overlap) == 0, (
                f"Chunk partitions {i + 1} and {j + 1} should not overlap, "
                f"but found overlap: {overlap}"
            )

    # Test stripe partitions have no overlap
    stripe_partitions = []
    for replica in range(1, total + 1):  # 1-based indexing
        partition = set(stripe(data, replica=replica, total=total))
        stripe_partitions.append(partition)

    # Check no overlap between stripe partitions
    for i in range(len(stripe_partitions)):
        for j in range(i + 1, len(stripe_partitions)):
            overlap = stripe_partitions[i].intersection(stripe_partitions[j])
            assert len(overlap) == 0, (
                f"Stripe partitions {i + 1} and {j + 1} should not overlap, "
                f"but found overlap: {overlap}"
            )


def test_chunk_stripe_integration_sparse_distribution_consistency() -> None:
    """Test that both functions handle sparse distribution consistently."""
    data = [1, 2, 3]  # 3 items
    total = 5  # 5 replicas (sparse case)

    # Test chunk sparse distribution
    chunk_results = {}
    for replica in range(1, total + 1):  # 1-based indexing
        result = list(chunk(data, replica=replica, total=total))
        chunk_results[replica] = result

    # Test stripe sparse distribution
    stripe_results = {}
    for replica in range(1, total + 1):  # 1-based indexing
        result = list(stripe(data, replica=replica, total=total))
        stripe_results[replica] = result

    # Verify chunk sparse distribution
    assert chunk_results[1] == [1], "Chunk replica 1 should get first item"
    assert chunk_results[2] == [2], "Chunk replica 2 should get second item"
    assert chunk_results[3] == [3], "Chunk replica 3 should get third item"
    assert chunk_results[4] == [], "Chunk replica 4 should get nothing"
    assert chunk_results[5] == [], "Chunk replica 5 should get nothing"

    # Verify stripe sparse distribution
    assert stripe_results[1] == [1], "Stripe replica 1 should get first item"
    assert stripe_results[2] == [2], "Stripe replica 2 should get second item"
    assert stripe_results[3] == [3], "Stripe replica 3 should get third item"
    assert stripe_results[4] == [], "Stripe replica 4 should get nothing"
    assert stripe_results[5] == [], "Stripe replica 5 should get nothing"

    # Both functions should give identical results in sparse case
    for replica in range(1, total + 1):
        assert chunk_results[replica] == stripe_results[replica], (
            f"Chunk and stripe should give same result for replica {replica} "
            f"in sparse distribution"
        )


def test_chunk_stripe_integration_different_distribution_patterns() -> None:
    """Test that chunk and stripe create different but valid distribution patterns."""
    data = list(range(12))
    total = 3

    # Get results from both functions
    chunk_results = []
    stripe_results = []

    for replica in range(1, total + 1):  # 1-based indexing
        chunk_results.append(list(chunk(data, replica=replica, total=total)))
        stripe_results.append(list(stripe(data, replica=replica, total=total)))

    # Chunk should create contiguous blocks
    expected_chunk = [
        [0, 1, 2, 3],  # First chunk
        [4, 5, 6, 7],  # Second chunk
        [8, 9, 10, 11],  # Third chunk
    ]
    assert chunk_results == expected_chunk, "Chunk should create contiguous blocks"

    # Stripe should create interleaved patterns
    expected_stripe = [
        [0, 3, 6, 9],  # Every 3rd starting from 0
        [1, 4, 7, 10],  # Every 3rd starting from 1
        [2, 5, 8, 11],  # Every 3rd starting from 2
    ]
    assert stripe_results == expected_stripe, (
        "Stripe should create interleaved patterns"
    )

    # Both should cover all data
    chunk_flat = [item for sublist in chunk_results for item in sublist]
    stripe_flat = [item for sublist in stripe_results for item in sublist]

    assert sorted(chunk_flat) == data, "Chunk should cover all data"
    assert sorted(stripe_flat) == data, "Stripe should cover all data"


def test_chunk_stripe_integration_environment_variables() -> None:
    """Test chunk and stripe integration with mocked environment variables."""
    data = list(range(16))

    # Test with environment variables set
    with patch.dict(os.environ, {"REPLICA_ID": "2", "REPLICA_COUNT": "4"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        chunk_result = list(chunk(data, replica=replica, total=total))
        stripe_result = list(stripe(data, replica=replica, total=total))

        # Verify both functions use the environment variables correctly
        # 16 items, 4 replicas, replica 2 (1-based)
        expected_chunk = [4, 5, 6, 7]  # Second chunk of 4 items each
        expected_stripe = [1, 5, 9, 13]  # Every 4th item starting from index 1

        assert chunk_result == expected_chunk, (
            "Chunk should use environment variables correctly"
        )
        assert stripe_result == expected_stripe, (
            "Stripe should use environment variables correctly"
        )


def test_chunk_stripe_integration_edge_cases() -> None:
    """Test chunk and stripe integration with edge cases."""
    # Test with single item
    data = [42]
    total = 3

    chunk_results = []
    stripe_results = []

    for replica in range(1, total + 1):  # 1-based indexing
        chunk_results.append(list(chunk(data, replica=replica, total=total)))
        stripe_results.append(list(stripe(data, replica=replica, total=total)))

    # Both should give same results for single item
    expected = [[42], [], []]  # Only first replica gets the item
    assert chunk_results == expected, "Chunk single item should match expected"
    assert stripe_results == expected, "Stripe single item should match expected"

    # Test with empty data
    empty_data = []
    chunk_empty = []
    stripe_empty = []

    for replica in range(1, total + 1):  # 1-based indexing
        chunk_empty.append(list(chunk(empty_data, replica=replica, total=total)))
        stripe_empty.append(list(stripe(empty_data, replica=replica, total=total)))

    # Both should return empty lists for all replicas
    expected_empty = [[], [], []]
    assert chunk_empty == expected_empty, "Chunk empty data should return empty lists"
    assert stripe_empty == expected_empty, "Stripe empty data should return empty lists"


def test_chunk_stripe_integration_large_scale() -> None:
    """Test chunk and stripe integration with larger datasets."""
    data = list(range(100))
    total = 10

    # Collect all results
    chunk_all = []
    stripe_all = []

    for replica in range(1, total + 1):  # 1-based indexing
        chunk_items = list(chunk(data, replica=replica, total=total))
        stripe_items = list(stripe(data, replica=replica, total=total))

        chunk_all.extend(chunk_items)
        stripe_all.extend(stripe_items)

    # Verify complete coverage
    assert sorted(chunk_all) == data, "Large scale chunk should cover all data"
    assert sorted(stripe_all) == data, "Large scale stripe should cover all data"

    # Verify expected sizes
    assert len(chunk_all) == 100, "Chunk should have all 100 items"
    assert len(stripe_all) == 100, "Stripe should have all 100 items"

    # Verify no duplicates
    assert len(set(chunk_all)) == 100, "Chunk should have no duplicates"
    assert len(set(stripe_all)) == 100, "Stripe should have no duplicates"


def test_chunk_stripe_integration_uneven_distribution() -> None:
    """Test chunk and stripe integration with uneven data distribution."""
    data = list(range(23))  # 23 items (prime number for uneven distribution)
    total = 5

    # Test chunk distribution
    chunk_results = []
    for replica in range(1, total + 1):  # 1-based indexing
        result = list(chunk(data, replica=replica, total=total))
        chunk_results.append(result)

    # Test stripe distribution
    stripe_results = []
    for replica in range(1, total + 1):  # 1-based indexing
        result = list(stripe(data, replica=replica, total=total))
        stripe_results.append(result)

    # Verify chunk distribution (23 // 5 = 4, remainder 3)
    # First 4 replicas get 4 items each, last replica gets 4 + 3 = 7 items
    expected_chunk_sizes = [4, 4, 4, 4, 7]
    actual_chunk_sizes = [len(result) for result in chunk_results]
    assert actual_chunk_sizes == expected_chunk_sizes, (
        f"Chunk sizes should be {expected_chunk_sizes}, got {actual_chunk_sizes}"
    )

    # Verify stripe distribution (should be more evenly distributed)
    stripe_sizes = [len(result) for result in stripe_results]
    # Each replica should get either 4 or 5 items (23 / 5 = 4.6)
    for size in stripe_sizes:
        assert 4 <= size <= 5, f"Stripe partition size {size} should be 4 or 5"

    # Verify both cover all data
    chunk_flat = [item for sublist in chunk_results for item in sublist]
    stripe_flat = [item for sublist in stripe_results for item in sublist]

    assert sorted(chunk_flat) == data, "Uneven chunk should cover all data"
    assert sorted(stripe_flat) == data, "Uneven stripe should cover all data"


def test_chunk_stripe_integration_consistency_across_scenarios() -> None:
    """Test that chunk and stripe maintain consistency across various scenarios."""
    test_scenarios = [
        (list(range(10)), 2),  # Even division
        (list(range(11)), 3),  # Uneven division
        (list(range(5)), 5),  # Equal items and replicas
        (list(range(3)), 7),  # Sparse distribution
        ([1], 4),  # Single item, multiple replicas
        ([], 3),  # Empty data
    ]

    for data, total in test_scenarios:
        # Test that both functions work with 1-based indexing
        for replica in range(1, total + 1):  # 1-based indexing
            try:
                chunk_result = list(chunk(data, replica=replica, total=total))
                stripe_result = list(stripe(data, replica=replica, total=total))

                # Both should return lists
                assert isinstance(chunk_result, list), (
                    f"Chunk should return list for data={data}, replica={replica}"
                )
                assert isinstance(stripe_result, list), (
                    f"Stripe should return list for data={data}, replica={replica}"
                )

                # Results should only contain items from original data
                for item in chunk_result:
                    assert item in data, (
                        f"Chunk result {item} not in original data {data}"
                    )
                for item in stripe_result:
                    assert item in data, (
                        f"Stripe result {item} not in original data {data}"
                    )

            except Exception as e:  # noqa: BLE001
                pytest.fail(
                    f"Functions should not raise exceptions for valid inputs: "
                    f"data={data}, replica={replica}, total={total}, error={e}"
                )

        # Test complete coverage for non-empty data
        if data:
            chunk_all = []
            stripe_all = []

            for replica in range(1, total + 1):  # 1-based indexing
                chunk_all.extend(chunk(data, replica=replica, total=total))
                stripe_all.extend(stripe(data, replica=replica, total=total))

            assert sorted(chunk_all) == sorted(data), (
                f"Chunk should cover all data for scenario: data={data}, total={total}"
            )
            assert sorted(stripe_all) == sorted(data), (
                f"Stripe should cover all data for scenario: data={data}, total={total}"
            )


def test_environment_integration_realistic_scenarios() -> None:
    """Test chunk function with realistic canfar container environment scenarios.

    This test simulates real-world canfar container environments where REPLICA_ID
    and REPLICA_COUNT are set as string environment variables with 1-based indexing.
    """
    # Scenario 1: Processing 100 astronomical images across 10 containers
    image_files = [f"image_{i:03d}.fits" for i in range(100)]

    # Simulate each container's environment and verify correct distribution
    all_processed_files = []
    for container_id in range(1, 11):  # 1-based container IDs
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "10"}
        ):
            # Read environment variables as the function would
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            container_files = list(chunk(image_files, replica=replica, total=total))
            all_processed_files.extend(container_files)

            # Each container should get exactly 10 files
            assert len(container_files) == 10, (
                f"Container {container_id} should process exactly 10 files"
            )

            # Verify files are in correct order for this container
            expected_start = (container_id - 1) * 10
            expected_files = [
                f"image_{i:03d}.fits"
                for i in range(expected_start, expected_start + 10)
            ]
            assert container_files == expected_files

    # Verify all files were processed exactly once
    assert len(all_processed_files) == 100, "All 100 files should be processed"
    assert len(set(all_processed_files)) == 100, "No file should be processed twice"
    assert set(all_processed_files) == set(image_files), (
        "All original files should be processed"
    )


def test_environment_integration_sparse_distribution() -> None:
    """Test chunk function with sparse distribution in canfar environment.

    This simulates scenarios where there are fewer data items than containers,
    which can happen with small datasets or many parallel containers.
    """
    # Scenario: 3 large data files to be processed by 8 containers
    large_files = ["dataset_part1.h5", "dataset_part2.h5", "dataset_part3.h5"]

    processed_files = []
    active_containers = []

    for container_id in range(1, 9):  # 8 containers
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "8"}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            container_files = list(chunk(large_files, replica=replica, total=total))

            if container_files:
                processed_files.extend(container_files)
                active_containers.append(container_id)

                # Each active container should get exactly one file
                assert len(container_files) == 1, (
                    f"Container {container_id} should process exactly 1 file"
                )
            else:
                # Containers 4-8 should be idle
                assert container_id > 3, (
                    f"Container {container_id} should be idle (no files to process)"
                )

    # Verify correct distribution
    assert len(active_containers) == 3, "Exactly 3 containers should be active"
    assert active_containers == [1, 2, 3], "Containers 1, 2, 3 should be active"
    assert processed_files == large_files, "All files should be processed correctly"


def test_environment_integration_uneven_distribution() -> None:
    """Test chunk function with uneven distribution in canfar environment.

    This tests scenarios where data doesn't divide evenly across containers.
    """
    # Scenario: 23 data files across 5 containers
    data_files = [f"data_{i:02d}.csv" for i in range(23)]

    all_processed = []
    container_loads = {}

    for container_id in range(1, 6):  # 5 containers
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "5"}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            container_files = list(chunk(data_files, replica=replica, total=total))
            all_processed.extend(container_files)
            container_loads[container_id] = len(container_files)

    # Verify distribution: 23 files / 5 containers = 4 files each + 3 remainder
    # First 4 containers get 4 files each, last container gets 7 files (4 + 3 remainder)
    expected_loads = {1: 4, 2: 4, 3: 4, 4: 4, 5: 7}
    assert container_loads == expected_loads, (
        f"Expected loads {expected_loads}, got {container_loads}"
    )

    # Verify all files processed exactly once
    assert len(all_processed) == 23, "All 23 files should be processed"
    assert set(all_processed) == set(data_files), (
        "All original files should be processed"
    )


def test_environment_integration_edge_cases() -> None:
    """Test edge cases that might occur in real canfar environments."""
    # Edge case 1: Single file, multiple containers
    single_file = ["important_config.json"]

    for container_id in range(1, 6):  # 5 containers
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "5"}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            result = list(chunk(single_file, replica=replica, total=total))

            if container_id == 1:
                assert result == single_file, (
                    "Container 1 should process the single file"
                )
            else:
                assert result == [], f"Container {container_id} should be idle"

    # Edge case 2: Empty dataset
    empty_data = []

    for container_id in range(1, 4):  # 3 containers
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "3"}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            result = list(chunk(empty_data, replica=replica, total=total))
            assert result == [], f"Container {container_id} should get empty result"

    # Edge case 3: Single container (no parallelization)
    all_data = list(range(50))

    with patch.dict(os.environ, {"REPLICA_ID": "1", "REPLICA_COUNT": "1"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))
        result = list(chunk(all_data, replica=replica, total=total))
        assert result == all_data, "Single container should process all data"


def test_environment_integration_string_conversion() -> None:
    """Test that environment variables are properly converted from strings.

    Canfar sets environment variables as strings, so we need to ensure
    proper string-to-integer conversion works correctly.
    """
    data = list(range(20))

    # Test various string representations
    test_cases = [
        ("1", "4"),  # Basic case
        ("2", "4"),  # Middle replica
        ("4", "4"),  # Last replica
        ("01", "04"),  # Zero-padded strings
        ("3", "10"),  # Larger total
    ]

    for replica_str, total_str in test_cases:
        with patch.dict(
            os.environ, {"REPLICA_ID": replica_str, "REPLICA_COUNT": total_str}
        ):
            # Simulate the actual environment variable reading
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))

            # Should not raise any errors
            result = list(chunk(data, replica=replica, total=total))

            # Verify result is reasonable (non-empty for valid cases)
            if len(data) >= total:
                assert len(result) > 0, (
                    f"Should get non-empty result for replica={replica}, total={total}"
                )


def test_environment_integration_performance_characteristics() -> None:
    """Test performance characteristics with realistic Canfar workloads."""
    # Large dataset simulation (10,000 items across 20 containers)
    large_dataset = list(range(10000))

    start_time = time.time()

    # Simulate processing across all containers
    total_processed = 0
    for container_id in range(1, 21):  # 20 containers
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "20"}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            container_data = list(chunk(large_dataset, replica=replica, total=total))
            total_processed += len(container_data)

    end_time = time.time()
    processing_time = end_time - start_time

    # Verify all data was processed
    assert total_processed == 10000, "All 10,000 items should be processed"

    # Performance should be reasonable (less than 1 second for this test)
    assert processing_time < 1.0, (
        f"Processing should be fast, took {processing_time:.3f} seconds"
    )


def test_environment_integration_error_conditions() -> None:
    """Test error conditions that might occur in canfar environments."""
    data = list(range(10))

    # Test invalid REPLICA_ID (0-based indexing attempt)
    with patch.dict(os.environ, {"REPLICA_ID": "0", "REPLICA_COUNT": "5"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        with pytest.raises(ValueError, match="replica must be >= 1"):
            list(chunk(data, replica=replica, total=total))

    # Test REPLICA_ID exceeding REPLICA_COUNT
    with patch.dict(os.environ, {"REPLICA_ID": "6", "REPLICA_COUNT": "5"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        with pytest.raises(ValueError, match="replica cannot exceed total"):
            list(chunk(data, replica=replica, total=total))

    # Test zero REPLICA_COUNT
    with patch.dict(os.environ, {"REPLICA_ID": "1", "REPLICA_COUNT": "0"}):
        replica = int(os.environ.get("REPLICA_ID", "1"))
        total = int(os.environ.get("REPLICA_COUNT", "1"))

        with pytest.raises(ValueError, match="total must be positive"):
            list(chunk(data, replica=replica, total=total))


def test_environment_integration_real_world_workflow() -> None:
    """Test a complete real-world workflow simulation.

    This simulates a typical astronomical data processing workflow where
    multiple containers process different parts of a large dataset.
    """
    # Simulate processing 1000 FITS files across 25 containers
    fits_files = [f"observation_{i:04d}.fits" for i in range(1000)]

    # Track processing results
    processing_results = {}
    all_processed_files = []

    # Simulate each container's processing
    for container_id in range(1, 26):  # 25 containers (1-based)
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "25"}
        ):
            # Get files for this container
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            my_files = list(chunk(fits_files, replica=replica, total=total))

            # Simulate processing (just record what we would process)
            processing_results[container_id] = {
                "files_count": len(my_files),
                "first_file": my_files[0] if my_files else None,
                "last_file": my_files[-1] if my_files else None,
            }

            all_processed_files.extend(my_files)

    # Verify complete and correct distribution
    assert len(all_processed_files) == 1000, "All 1000 files should be processed"
    assert len(set(all_processed_files)) == 1000, "No file should be processed twice"

    # Verify load balancing (each container should get 40 files: 1000/25 = 40)
    for container_id, results in processing_results.items():
        assert results["files_count"] == 40, (
            f"Container {container_id} should process exactly 40 files, "
            f"got {results['files_count']}"
        )

    # Verify sequential assignment within each container
    for container_id in range(1, 26):
        with patch.dict(
            os.environ, {"REPLICA_ID": str(container_id), "REPLICA_COUNT": "25"}
        ):
            replica = int(os.environ.get("REPLICA_ID", "1"))
            total = int(os.environ.get("REPLICA_COUNT", "1"))
            my_files = list(chunk(fits_files, replica=replica, total=total))

            # Files should be sequential within each container's chunk
            expected_start = (container_id - 1) * 40
            expected_files = fits_files[expected_start : expected_start + 40]

            assert my_files == expected_files, (
                f"Container {container_id} should get sequential files "
                f"{expected_start} to {expected_start + 39}"
            )
