"""Root commands contributed by ``canfar.commands`` entry points."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator
from typer.main import get_command
from typer.testing import CliRunner

from canfar.cli.main import cli

_DEMO = "tests.cli_plugin_demo"
_RUNNER = CliRunner()


class _Metadata:
    """Stand-in for a distribution's metadata mapping."""

    def __init__(self, summary: str) -> None:
        """Store the Summary field the loader reads."""
        self._summary = summary

    def get(self, key: str, default: str = "") -> str:
        """Return Summary, or ``default`` for every other field."""
        if key == "Summary":
            return self._summary
        return default


class _Dist:
    """Stand-in for an installed distribution."""

    def __init__(self, summary: str) -> None:
        """Attach metadata with the given summary."""
        self.metadata = _Metadata(summary)


class _EntryPoint:
    """Entry point the loader can read without calling ``load``."""

    def __init__(self, name: str, summary: str) -> None:
        """Point at the demo Typer app."""
        self.name = name
        self.value = f"{_DEMO}:app"
        self.dist = _Dist(summary)


def _install(monkeypatch: pytest.MonkeyPatch, *points: _EntryPoint) -> None:
    """Replace entry-point discovery for one test."""

    def entry_points(**kwargs: object) -> list[_EntryPoint]:
        if kwargs.get("group") == "canfar.commands":
            return list(points)
        return []

    monkeypatch.setattr(
        "canfar.cli.main.importlib.metadata.entry_points",
        entry_points,
    )


def _forget_plugin(name: str) -> None:
    """Drop a command the loader attached to the process-wide Click group."""
    get_command(cli).commands.pop(name, None)


@pytest.fixture
def _plug() -> Iterator[None]:
    """Remove the demo command if a test invoked it."""
    yield
    _forget_plugin("plug")


def test_root_help_lists_plugin_without_importing_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Help shows the distribution summary and does not import the plugin."""
    sys.modules.pop(_DEMO, None)
    _install(monkeypatch, _EntryPoint("plug", "Demo extension."))

    result = _RUNNER.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.stdout
    assert "plug" in result.stdout
    assert "Demo extension." in result.stdout
    assert _DEMO not in sys.modules


@pytest.mark.usefixtures("_plug")
def test_invoking_plugin_imports_its_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """Running the command loads the entry-point target."""
    sys.modules.pop(_DEMO, None)
    _install(monkeypatch, _EntryPoint("plug", "Demo extension."))

    result = _RUNNER.invoke(cli, ["plug"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "plugin-ok" in result.stdout
    assert _DEMO in sys.modules


def test_builtin_name_hides_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    """A plugin cannot replace a command the client already ships."""
    sys.modules.pop(_DEMO, None)
    _install(monkeypatch, _EntryPoint("version", "Demo extension."))

    result = _RUNNER.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.stdout
    assert "View client info" in result.stdout
    assert "Demo extension." not in result.stdout
    assert _DEMO not in sys.modules
