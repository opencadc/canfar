"""Tests that CLI startup loads only what the invoked command needs."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest
import typer
from typer.main import get_command

from canfar.cli.main import _COMMANDS, cli

DEFERRED = (
    "authlib",
    "canfar.authentication",
    "canfar.client",
    "canfar.server",
    "fsspec",
    "fsspec_cli",
    "httpx2",
    "segno",
)
"""Libraries and modules loaded only by the commands that use them."""


def _loaded_after(code: str) -> dict[str, list[str]]:
    """Run ``code`` in a fresh interpreter and report what it imported."""
    probe = (
        "import json, sys\n"
        f"{code}\n"
        "print(json.dumps({"
        f"'deferred': [name for name in {list(DEFERRED)!r} if name in sys.modules],"
        "'commands': sorted(name for name in sys.modules"
        " if name.startswith('canfar.cli.') and name not in"
        " {'canfar.cli.main', 'canfar.cli.output'})"
        "}), file=sys.stderr)"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe],
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stderr.strip().splitlines()[-1])


@pytest.mark.parametrize(
    "code",
    [
        "import canfar.cli.main",
        (
            "sys.argv = ['canfar', '--help']\n"
            "from canfar.cli.main import main\n"
            "try:\n    main()\nexcept SystemExit:\n    pass"
        ),
    ],
    ids=["import", "root-help"],
)
def test_cli_startup_loads_no_command_dependencies(code: str) -> None:
    """Importing the CLI and listing its commands imports no command module."""
    assert _loaded_after(code) == {"deferred": [], "commands": []}


def test_a_command_loads_only_its_own_module() -> None:
    """Running ``version`` imports its module but not the others."""
    loaded = _loaded_after(
        "sys.argv = ['canfar', 'version']\n"
        "from canfar.cli.main import main\n"
        "try:\n    main()\nexcept SystemExit:\n    pass"
    )

    assert loaded["commands"] == ["canfar.cli.version"]


def test_every_root_command_loads_as_root_help_lists_it() -> None:
    """Each registry target resolves to the command root help describes."""
    root = get_command(cli)
    ctx = typer.Context(root)

    # Commands registered directly on ``cli`` (as other tests do) follow these.
    assert root.list_commands(ctx)[: len(_COMMANDS)] == list(_COMMANDS)
    for name, registration in _COMMANDS.items():
        command = root.get_command(ctx, name)
        assert command is not None, name
        assert (command.name, command.help) == (name, registration.help)
        assert getattr(command, "rich_help_panel", None) == registration.panel
