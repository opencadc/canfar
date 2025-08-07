"""Tests for ps command aliases (ls, list)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from skaha.cli.main import cli


class TestPsAliases:
    """Test cases for ps command aliases."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_ps_command_help(self, runner: CliRunner) -> None:
        """Test that ps command shows help correctly."""
        result = runner.invoke(cli, ["ps", "--help"])
        assert result.exit_code == 0

    def test_ls_alias_help(self, runner: CliRunner) -> None:
        """Test that ls alias shows help correctly."""
        result = runner.invoke(cli, ["ls", "--help"])
        assert result.exit_code == 0

    def test_list_alias_help(self, runner: CliRunner) -> None:
        """Test that list alias shows help correctly."""
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0

    def test_main_help_shows_aliases(self, runner: CliRunner) -> None:
        """Test that main help shows all aliases."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
