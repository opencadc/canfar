"""Root CLI composition contracts for issue #255."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import click
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()


def test_root_help_lists_leaf_commands_without_alias_section() -> None:
    """Canonical leaf commands stay at the root and aliases disappear."""
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    for command in (
        "create",
        "ps",
        "events",
        "info",
        "open",
        "logs",
        "delete",
        "prune",
        "stats",
        "version",
    ):
        assert command in result.stdout
    assert "Aliases" not in result.stdout
    assert "Alias for auth" not in result.stdout
    assert "run | launch" not in result.stdout
    assert "del           " not in result.stdout


def test_management_groups_remain_grouped() -> None:
    """Authentication and server management retain their subcommands."""
    root = get_command(cli)
    auth_result = runner.invoke(cli, ["auth", "--help"])
    server_result = runner.invoke(cli, ["server", "--help"])

    assert isinstance(root.commands["auth"], TyperGroup)
    assert isinstance(root.commands["server"], TyperGroup)
    assert auth_result.exit_code == 0
    assert "show" in auth_result.stdout
    assert "ls" in auth_result.stdout
    assert "use" in auth_result.stdout
    assert server_result.exit_code == 0
    assert "ls" in server_result.stdout
    assert "use" in server_result.stdout


def test_session_and_information_leaves_are_root_commands() -> None:
    """Leaf callbacks are commands, not one-callback child groups."""
    root = get_command(cli)

    for name in (
        "create",
        "ps",
        "events",
        "info",
        "open",
        "logs",
        "delete",
        "prune",
        "stats",
        "version",
    ):
        assert name in root.commands
        assert not isinstance(root.commands[name], TyperGroup)


def test_removed_root_aliases_are_usage_errors() -> None:
    """Removed root aliases fail with Click's standard usage exit code."""
    for alias in ("authentication", "run", "launch", "del"):
        result = runner.invoke(cli, [alias, "--help"])
        assert result.exit_code == 2
        assert f"No such command '{alias}'" in result.output


def test_create_root_usage_preserves_delimiter_contract() -> None:
    """The root create command reserves every token after ``--``."""
    result = runner.invoke(
        cli,
        [
            "create",
            "--dry-run",
            "headless",
            "example.invalid/image",
            "--",
            "echo",
            "--output",
            "json",
            "-o",
            "yaml",
        ],
    )

    assert result.exit_code == 0
    assert "Command: echo" in result.stdout
    assert "Arguments: --output json -o yaml" in result.stdout


@patch("canfar.cli.create.AsyncSession")
def test_root_create_output_stops_at_delimiter(mock_session_cls: AsyncMock) -> None:
    """Root create parses output before ``--`` and reserves the rest."""
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session
    mock_session.create.return_value = ["session-id"]

    result = runner.invoke(
        cli,
        [
            "create",
            "headless",
            "example.invalid/image",
            "--output",
            "json",
            "--",
            "echo",
            "-o",
            "yaml",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout) == ["session-id"]
    request = mock_session.create.await_args.args[0]
    assert request.cmd == "echo"
    assert request.args == "-o yaml --output json"


def test_root_leaf_help_keeps_canonical_usage() -> None:
    """Direct leaf commands retain their documented usage lines."""
    create_result = runner.invoke(cli, ["create", "--help"])
    prune_result = runner.invoke(cli, ["prune", "--help"])
    create_help = " ".join(click.unstyle(create_result.stdout).split())
    prune_help = " ".join(click.unstyle(prune_result.stdout).split())

    assert create_result.exit_code == 0
    assert "Usage: canfar create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]" in create_help
    assert prune_result.exit_code == 0
    prune_usage = "Usage: canfar prune [OPTIONS] PREFIX KIND STATUS COMMAND [ARGS]..."
    assert prune_usage in prune_help
