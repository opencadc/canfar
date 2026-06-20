"""Characterization tests guarding the dead-module cleanup (issue #137).

Two empty placeholder modules (``canfar/cli/run.py`` and ``canfar/cli/alias.py``)
are removed by this cleanup. Neither is imported anywhere; the ``run``/``launch``
and ``del`` CLI aliases are wired in :mod:`canfar.cli.main` via the
:class:`~canfar.hooks.typer.aliases.AliasGroup`, not by those files. These tests
pin both invariants so the deletion cannot silently regress the alias feature.
"""

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


@pytest.mark.parametrize("alias", ["run", "launch", "del"])
def test_cli_aliases_still_resolve(alias: str) -> None:
    """The ``run``/``launch``/``del`` aliases keep resolving through the app."""
    result = runner.invoke(cli, [alias, "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
