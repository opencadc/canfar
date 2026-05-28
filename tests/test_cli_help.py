"""Test CLI commands with --help option."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()

COMMANDS = [
    [],
    ["login"],
    ["auth"],
    ["auth", "login"],
    ["auth", "ls"],
    ["auth", "use"],
    ["auth", "remove"],
    ["auth", "purge"],
    ["server", "ls"],
    ["server", "use"],
    ["context", "show"],
    ["context", "ls"],
    ["config"],
    ["config", "list"],
    ["config", "path"],
    ["create"],
    ["delete"],
    ["events"],
    ["info"],
    ["logs"],
    ["prune"],
    ["ps"],
    ["stats"],
    ["version"],
]


@pytest.mark.parametrize("command", COMMANDS)
def test_cli_help(command: list[str]) -> None:
    """Test CLI commands with --help option."""
    result = runner.invoke(cli, [*command, "--help"])
    assert result.exit_code == 0
