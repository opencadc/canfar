"""Tests for removed CLI placeholder modules and aliases."""

from __future__ import annotations

import importlib.util

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()


@pytest.mark.parametrize("module", ["canfar.cli.run", "canfar.cli.alias"])
def test_dead_cli_module_is_absent(module: str) -> None:
    """The empty placeholder modules must not be importable after cleanup."""
    assert importlib.util.find_spec(module) is None


@pytest.mark.parametrize("alias", ["authentication", "run", "launch", "del"])
def test_removed_cli_aliases_do_not_resolve(alias: str) -> None:
    """The old root aliases are no longer accepted by the app."""
    result = runner.invoke(cli, [alias, "--help"])
    assert result.exit_code == 2
    assert f"No such command '{alias}'" in result.output


def test_removed_auth_login_alias_does_not_resolve() -> None:
    """Authentication management keeps canonical commands only."""
    result = runner.invoke(cli, ["auth", "login", "--help"])
    assert result.exit_code == 2
    assert "No such command 'login'" in result.output
