"""Root commands contributed by ``canfar.commands`` entry points."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path

_DEMO = "tests.cli_plugin_demo"
_RUNNER = CliRunner()


def _install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "plug",
    value: str = f"{_DEMO}:app",
    summary: str = "Demo extension.",
) -> None:
    """Expose real distribution metadata without installing a package."""
    dist = tmp_path / f"{name}_demo-1.0.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}-demo\nVersion: 1.0\nSummary: {summary}\n",
        encoding="utf-8",
    )
    (dist / "entry_points.txt").write_text(
        f"[canfar.commands]\n{name} = {value}\n", encoding="utf-8"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, _DEMO, raising=False)


@pytest.mark.parametrize("summary", ["Demo extension.", ""])
def test_root_help_lists_plugin_without_importing_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, summary: str
) -> None:
    """Help shows the distribution summary and does not import the plugin."""
    _install(tmp_path, monkeypatch, summary=summary)

    result = _RUNNER.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.stdout
    assert "Extensions" in result.stdout
    assert "plug" in result.stdout
    assert (summary or "Installed extension.") in result.stdout
    assert _DEMO not in sys.modules


@pytest.mark.parametrize("target", ["app", "commands.app", "app [extra]", " app "])
def test_invoking_plugin_loads_entry_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    """Invocation resolves standard entry-point targets and imports the app."""
    _install(tmp_path, monkeypatch, value=f"{_DEMO}:{target}")

    result = _RUNNER.invoke(cli, ["plug"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "plugin-ok" in result.stdout
    assert _DEMO in sys.modules


def test_builtin_name_hides_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A plugin cannot replace a command the client already ships."""
    _install(tmp_path, monkeypatch, name="version", value="missing_plugin:app")

    result = _RUNNER.invoke(cli, ["--help"])

    assert result.exit_code == 0, result.stdout
    assert "View client info" in result.stdout
    assert "Demo extension." not in result.stdout
    assert _RUNNER.invoke(cli, ["version"]).exit_code == 0
    assert "missing_plugin" not in sys.modules


@pytest.mark.parametrize("value", [f"{_DEMO}:app", "missing_plugin:app"])
def test_root_completion_does_not_import_plugin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """Root completion lists even unloadable plugins alongside built-ins."""
    _install(tmp_path, monkeypatch, value=value)

    result = _RUNNER.invoke(
        cli,
        [],
        prog_name="canfar",
        env={
            "_CANFAR_COMPLETE": "complete_bash",
            "COMP_WORDS": "canfar ",
            "COMP_CWORD": "1",
        },
    )

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "plug" in result.stdout
    assert "version" in result.stdout
    assert _DEMO not in sys.modules


def test_completion_inside_plugin_loads_selected_app(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nested completion loads its app without importing another extension."""
    _install(tmp_path, monkeypatch)
    _install(tmp_path, monkeypatch, name="broken", value="missing_plugin:app")

    result = _RUNNER.invoke(
        cli,
        [],
        prog_name="canfar",
        env={
            "_CANFAR_COMPLETE": "complete_bash",
            "COMP_WORDS": "canfar plug h",
            "COMP_CWORD": "2",
        },
    )

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "hello" in result.stdout
    assert _DEMO in sys.modules
    assert "missing_plugin" not in sys.modules
