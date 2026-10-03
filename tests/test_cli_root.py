"""Root CLI composition contracts for issue #255."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import typer
from rich.text import Text
from typer.core import TyperGroup
from typer.main import get_command
from typer.testing import CliRunner

from canfar.cli.main import cli


def _root_command(name: str) -> object:
    """Resolve one root command the way invocation does, loading it on demand."""
    root = get_command(cli)
    return root.get_command(typer.Context(root), name)


runner = CliRunner()


def test_root_help_lists_leaf_commands_without_alias_section() -> None:
    """Canonical leaf commands remain discoverable at the root."""
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


def test_management_groups_remain_grouped() -> None:
    """Authentication and server management retain their subcommands."""
    auth_result = runner.invoke(cli, ["auth", "--help"])
    server_result = runner.invoke(cli, ["server", "--help"])

    assert isinstance(_root_command("auth"), TyperGroup)
    assert isinstance(_root_command("server"), TyperGroup)
    assert auth_result.exit_code == 0
    assert "show" in auth_result.stdout
    assert "ls" in auth_result.stdout
    assert "use" in auth_result.stdout
    assert server_result.exit_code == 0
    assert "ls" in server_result.stdout
    assert "use" in server_result.stdout


def test_session_and_information_leaves_are_root_commands() -> None:
    """Leaf callbacks are commands, not one-callback child groups."""
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
        command = _root_command(name)
        assert command is not None
        assert not isinstance(command, TyperGroup)


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
    create_help = " ".join(Text.from_ansi(create_result.stdout).plain.split())
    prune_help = " ".join(Text.from_ansi(prune_result.stdout).plain.split())

    assert create_result.exit_code == 0
    assert "Usage: canfar create [OPTIONS] KIND IMAGE [-- CMD [ARGS]...]" in create_help
    assert prune_result.exit_code == 0
    prune_usage = "Usage: canfar prune [OPTIONS] PREFIX KIND STATUS COMMAND [ARGS]..."
    assert prune_usage in prune_help
