"""Test main CLI entrypoint."""

from __future__ import annotations

from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()


def test_main_cli_no_subcommand() -> None:
    """Test main CLI entrypoint with no subcommand."""
    result = runner.invoke(cli)
    assert result.exit_code == 0


def test_main_cli_with_help_option() -> None:
    """Test main CLI entrypoint with --help option."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
