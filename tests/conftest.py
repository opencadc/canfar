"""Pytest configuration and fixtures for CANFAR tests."""

from __future__ import annotations

import os
import uuid

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "vos: marks tests as VOSpace integration tests"
    )


@pytest.fixture(scope="session")
def vos_base_uri() -> str:
    """Get the base VOSpace URI for testing.

    Can be overridden via VOS_TEST_URI environment variable.
    Default: vos://canfar.itsrc.oact.inaf.it~cavern/home/

    Returns:
        str: Base VOSpace URI for tests.
    """
    return os.environ.get(
        "VOS_TEST_URI",
        "vos://canfar.itsrc.oact.inaf.it~cavern/home/"
    )


@pytest.fixture(scope="session")
def vos_test_dir(vos_base_uri: str) -> str:
    """Generate a unique test directory path in VOSpace.

    Creates a unique directory name to avoid conflicts between test runs.

    Args:
        vos_base_uri: Base VOSpace URI.

    Returns:
        str: Unique test directory URI.
    """
    unique_id = uuid.uuid4().hex[:8]
    test_dir = f"{vos_base_uri.rstrip('/')}/test_canfar_{unique_id}/"
    return test_dir


@pytest.fixture(scope="session")
def local_test_file(tmp_path_factory) -> str:
    """Create a temporary local file for upload tests.

    Args:
        tmp_path_factory: Pytest temporary path factory.

    Returns:
        str: Path to local test file.
    """
    tmp_path = tmp_path_factory.mktemp("vos_test")
    test_file = tmp_path / "test_upload.txt"
    test_file.write_text("This is a test file for CANFAR VOS integration tests.\n")
    return str(test_file)


@pytest.fixture(scope="session")
def local_download_dir(tmp_path_factory) -> str:
    """Create a temporary directory for download tests.

    Args:
        tmp_path_factory: Pytest temporary path factory.

    Returns:
        str: Path to local download directory.
    """
    tmp_path = tmp_path_factory.mktemp("vos_download")
    return str(tmp_path)
