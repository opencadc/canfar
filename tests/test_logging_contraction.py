"""Help-text contracts for domain-specific debug flags."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from canfar.cli.main import cli

runner = CliRunner()
_HELP_ENV = {"COLUMNS": "120", "NO_COLOR": "1", "FORCE_COLOR": "0", "TERM": "dumb"}


@pytest.mark.parametrize(
    "command",
    [
        ["login"],
        ["auth", "login"],
        ["delete"],
        ["events"],
        ["logs"],
        ["open"],
        ["prune"],
        ["stats"],
    ],
)
def test_logging_only_leaf_debug_options_are_absent(command: list[str]) -> None:
    """Logging verbosity is controlled only by root options."""
    result = runner.invoke(cli, [*command, "--help"], env=_HELP_ENV, color=False)

    assert result.exit_code == 0, result.output
    assert "--debug" not in result.output


@pytest.mark.parametrize(
    ("command", "meaning"),
    [
        (["version"], "Show detailed information for bug reports."),
        (["info"], "Show Session response warnings."),
        (["ps"], "Show Session response warnings."),
        (["create"], "Print parsed Session request details."),
    ],
)
def test_domain_debug_options_keep_their_public_meanings(
    command: list[str],
    meaning: str,
) -> None:
    """Domain-specific debug flags remain visible and unambiguous."""
    result = runner.invoke(cli, [*command, "--help"], env=_HELP_ENV, color=False)

    assert result.exit_code == 0, result.output
    help_text = " ".join(result.output.replace("│", " ").split())
    assert "--debug" in help_text
    assert meaning in help_text
