"""Tests for the version CLI module."""

import pytest
from typer.testing import CliRunner

from canfar.cli.version import (
    version,
)


class TestVersionCLI:
    """Test cases for the version CLI functionality."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_version_simple_output(self, runner: CliRunner) -> None:
        """Test simple version output without debug flag."""
        result = runner.invoke(version, [])

        assert result.exit_code == 0
        assert "CANFAR Python Client" in result.stdout

    def test_version_debug_output(self, runner: CliRunner) -> None:
        """Test detailed debug output with --debug flag."""
        result = runner.invoke(version, ["--debug"])
        assert result.exit_code == 0
        assert "CANFAR Python Client Debug Information" in result.stdout
        assert "Client Version" in result.stdout
        assert "Python Version" in result.stdout
        assert "Python Executable" in result.stdout
        assert "Python Impl" in result.stdout
        assert "Operating System" in result.stdout
        assert "OS Version" in result.stdout
        assert "Architecture" in result.stdout
        assert "Platform" in result.stdout
        assert "Key Dependencies" in result.stdout
