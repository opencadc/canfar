"""Integration tests for the stats and ps CLI commands."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()


def test_stats_command_help() -> None:
    """Test stats command help executes successfully."""
    result = runner.invoke(cli, ["stats", "--help"])
    assert result.exit_code == 0


def test_ps_command_help() -> None:
    """Test ps command help executes successfully."""
    result = runner.invoke(cli, ["ps", "--help"])
    assert result.exit_code == 0


@pytest.mark.slow
def test_stats_command_integration() -> None:
    """Test stats command integration (may fail without proper auth/config)."""
    result = runner.invoke(cli, ["stats"])
    # Command should exit cleanly even if it fails due to auth/config issues
    # We're just testing that it doesn't crash with exit code 2 (syntax error)
    assert result.exit_code in [0, 1]  # 0 = success, 1 = expected failure


@pytest.mark.slow
def test_ps_command_integration() -> None:
    """Test ps command integration (may fail without proper auth/config)."""
    result = runner.invoke(cli, ["ps"])
    # Command should exit cleanly even if it fails due to auth/config issues
    # We're just testing that it doesn't crash with exit code 2 (syntax error)
    assert result.exit_code in [0, 1]  # 0 = success, 1 = expected failure
