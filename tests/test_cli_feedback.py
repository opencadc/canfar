"""Feedback remains available when the user's client cannot be configured."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("contents", [None, "[invalid yaml", "version: 1\n"])
def test_feedback_needs_no_configuration(monkeypatch, tmp_path: Path, contents) -> None:
    """Printing the link neither validates nor migrates a saved configuration."""
    config_path = tmp_path / "config.yaml"
    if contents is not None:
        config_path.write_text(contents, encoding="utf-8")
    monkeypatch.setattr("canfar.models.config.CONFIG_PATH", config_path)

    result = CliRunner().invoke(cli, ["feedback"])

    assert result.exit_code == 0, result.output
    assert result.stdout == "https://github.com/opencadc/canfar/issues/new/choose\n"
    assert result.stderr == ""
    if contents is None:
        assert not config_path.exists()
    else:
        assert config_path.read_text(encoding="utf-8") == contents
