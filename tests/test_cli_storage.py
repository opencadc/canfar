"""Integration tests for CANFAR storage CLI commands.

These tests require:
1. Valid CANFAR authentication (run `canfar auth login` first)
2. Access to a VOSpace server

Run with: pytest -m integration tests/test_cli_storage.py -v
Skip in CI: pytest -m "not integration"

Configure VOSpace URI via environment variable:
    export VOS_TEST_URI="vos://canfar.itsrc.oact.inaf.it~cavern/home/"
"""

from __future__ import annotations

import os

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli

# Use CliRunner with env to preserve authentication context (HOME, config paths, etc.)
runner = CliRunner(env=os.environ.copy())

# Store state between ordered tests
_test_state: dict = {}


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(1)
def test_storage_mkdir(vos_test_dir: str) -> None:
    """Test creating a directory in VOSpace."""
    _test_state["test_dir"] = vos_test_dir

    result = runner.invoke(cli, ["storage", "mkdir", vos_test_dir])

    assert result.exit_code == 0, f"mkdir failed: {result.output}"
    assert "Created" in result.output or result.exit_code == 0


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(2)
def test_storage_ls_empty_dir() -> None:
    """Test listing an empty directory in VOSpace."""
    test_dir = _test_state.get("test_dir")
    if not test_dir:
        pytest.skip("test_storage_mkdir must run first")

    result = runner.invoke(cli, ["storage", "ls", test_dir])

    # Empty directory should return success (exit code 0)
    # Output may be empty or just the directory name
    assert result.exit_code == 0, f"ls failed: {result.output}"


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(3)
def test_storage_cp_upload(local_test_file: str) -> None:
    """Test uploading a file to VOSpace."""
    test_dir = _test_state.get("test_dir")
    if not test_dir:
        pytest.skip("test_storage_mkdir must run first")

    destination = f"{test_dir}test_upload.txt"
    _test_state["uploaded_file"] = destination

    result = runner.invoke(cli, ["storage", "cp", local_test_file, destination])

    assert result.exit_code == 0, f"cp upload failed: {result.output}"


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(4)
def test_storage_ls_with_file() -> None:
    """Test listing a directory containing a file."""
    test_dir = _test_state.get("test_dir")
    if not test_dir:
        pytest.skip("test_storage_mkdir must run first")

    result = runner.invoke(cli, ["storage", "ls", test_dir])

    assert result.exit_code == 0, f"ls failed: {result.output}"
    assert "test_upload.txt" in result.output


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(5)
def test_storage_ls_long_format() -> None:
    """Test listing with long format (-l flag)."""
    test_dir = _test_state.get("test_dir")
    if not test_dir:
        pytest.skip("test_storage_mkdir must run first")

    result = runner.invoke(cli, ["storage", "ls", "-l", test_dir])

    assert result.exit_code == 0, f"ls -l failed: {result.output}"
    # Long format should show permissions and other details
    assert "test_upload.txt" in result.output


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(6)
def test_storage_cp_download(local_download_dir: str) -> None:
    """Test downloading a file from VOSpace."""
    uploaded_file = _test_state.get("uploaded_file")
    if not uploaded_file:
        pytest.skip("test_storage_cp_upload must run first")

    local_dest = os.path.join(local_download_dir, "downloaded.txt")
    _test_state["downloaded_file"] = local_dest

    result = runner.invoke(cli, ["storage", "cp", uploaded_file, local_dest])

    assert result.exit_code == 0, f"cp download failed: {result.output}"
    assert os.path.exists(local_dest), "Downloaded file not found"

    # Verify content
    with open(local_dest) as f:
        content = f.read()
    assert "test file for CANFAR VOS" in content


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(7)
def test_storage_rm_file() -> None:
    """Test removing a file from VOSpace."""
    uploaded_file = _test_state.get("uploaded_file")
    if not uploaded_file:
        pytest.skip("test_storage_cp_upload must run first")

    result = runner.invoke(cli, ["storage", "rm", uploaded_file])

    assert result.exit_code == 0, f"rm failed: {result.output}"
    assert "Deleted" in result.output


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(8)
def test_storage_ls_after_delete() -> None:
    """Test that deleted file no longer appears in listing."""
    test_dir = _test_state.get("test_dir")
    if not test_dir:
        pytest.skip("test_storage_mkdir must run first")

    result = runner.invoke(cli, ["storage", "ls", test_dir])

    assert result.exit_code == 0, f"ls failed: {result.output}"
    # File should no longer be listed
    assert "test_upload.txt" not in result.output


@pytest.mark.integration
@pytest.mark.vos
@pytest.mark.order(9)
def test_storage_rm_directory() -> None:
    """Test removing the test directory from VOSpace (cleanup).

    Note: Some VOSpace servers require authentication for recursive delete.
    This test will pass if directory is deleted, or warn if cleanup fails.
    """
    test_dir = _test_state.get("test_dir")
    if not test_dir:
        pytest.skip("test_storage_mkdir must run first")

    # Try recursive delete (required for directories via CLI)
    result = runner.invoke(cli, ["storage", "rm", "-R", test_dir])

    if result.exit_code != 0:
        # Some servers don't support recursive delete for anonymous/limited auth
        if "anonymous" in result.output.lower() or "authenticate" in result.output.lower():
            pytest.skip(
                "Server requires authentication for recursive delete. "
                f"Please manually clean up: {test_dir}"
            )
        else:
            pytest.fail(f"rm -R failed: {result.output}")


# Additional edge case tests


@pytest.mark.integration
@pytest.mark.vos
def test_storage_ls_invalid_uri() -> None:
    """Test ls with an invalid VOSpace URI."""
    result = runner.invoke(cli, ["storage", "ls", "invalid://not-a-vos-uri"])

    assert result.exit_code != 0
    assert "Error" in result.output or "Invalid" in result.output


@pytest.mark.integration
@pytest.mark.vos
def test_storage_ls_nonexistent_path(vos_base_uri: str) -> None:
    """Test ls on a path that doesn't exist."""
    nonexistent = f"{vos_base_uri.rstrip('/')}/nonexistent_path_12345/"

    result = runner.invoke(cli, ["storage", "ls", nonexistent])

    # Should fail with error
    assert result.exit_code != 0


@pytest.mark.integration
@pytest.mark.vos
def test_storage_help() -> None:
    """Test storage --help command."""
    result = runner.invoke(cli, ["storage", "--help"])

    assert result.exit_code == 0
    assert "Manage files in Cavern storage" in result.output
    assert "ls" in result.output
    assert "cp" in result.output
    assert "rm" in result.output
    assert "mkdir" in result.output


@pytest.mark.integration
@pytest.mark.vos
def test_storage_ls_help() -> None:
    """Test storage ls --help command."""
    result = runner.invoke(cli, ["storage", "ls", "--help"])

    assert result.exit_code == 0
    assert "List Cavern directory contents" in result.output


@pytest.mark.integration
@pytest.mark.vos
def test_storage_cp_help() -> None:
    """Test storage cp --help command."""
    result = runner.invoke(cli, ["storage", "cp", "--help"])

    assert result.exit_code == 0
    assert "Copy files to and from Cavern storage" in result.output


@pytest.mark.integration
@pytest.mark.vos
def test_storage_rm_help() -> None:
    """Test storage rm --help command."""
    result = runner.invoke(cli, ["storage", "rm", "--help"])

    assert result.exit_code == 0
    assert "Remove Cavern files or directories" in result.output


@pytest.mark.integration
@pytest.mark.vos
def test_storage_mkdir_help() -> None:
    """Test storage mkdir --help command."""
    result = runner.invoke(cli, ["storage", "mkdir", "--help"])

    assert result.exit_code == 0
    assert "Create a new Cavern directory" in result.output
