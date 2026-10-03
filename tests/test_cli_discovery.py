"""Tests for the live Server discovery grid."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console
from rich.text import Text

from canfar.cli.discovery import DiscoveryGrid
from canfar.models.registry import ServerProbe


def _probe(name: str, status: str) -> ServerProbe:
    return ServerProbe(
        name=name,
        uri=f"ivo://{name}.example/skaha",
        url=f"https://{name}.example/skaha",
        status=status,
    )


def _ansi(grid: DiscoveryGrid) -> str:
    """Render the grid on a color terminal, keeping the escape codes."""
    output = StringIO()
    Console(file=output, width=80, force_terminal=True, color_system="standard").print(
        grid
    )
    return output.getvalue()


def _render(grid: DiscoveryGrid, *, color: bool = False) -> list[str]:
    """Render the grid as text lines between its blank framing lines."""
    output = StringIO()
    console = (
        Console(file=output, width=80, force_terminal=True, color_system="truecolor")
        if color
        else Console(file=output, width=80, color_system=None)
    )
    console.print(grid)
    text = output.getvalue()
    lines = Text.from_ansi(text).plain.splitlines() if color else text.splitlines()
    if not lines:
        return []
    assert (lines[0], lines[-1]) == ("", "")
    return lines[1:-1]


def test_grid_waits_for_registries_before_showing_squares() -> None:
    """Before any Server is listed, the grid shows only progress."""
    assert _render(DiscoveryGrid("srcnet", timeout=10)) == [
        "Discovering srcnet servers... 0s"
    ]


def test_color_grid_shows_squares_filling_in_as_outcomes_arrive() -> None:
    """On a color terminal, pending Servers are hollow squares."""
    grid = DiscoveryGrid("srcnet", timeout=10)
    for name in ("ukRAL", "canSRC", "cnSRC"):
        grid.update(_probe(name, "pending"))
    grid.update(_probe("cnSRC", "unreachable"))

    assert _render(grid, color=True) == [
        "□ ■ □",
        "■ 0 discovered   ■ 0 timeout   ■ 1 unreachable   ■ 0 failed   □ 2 pending",
        "Checking 3 servers... 0s",
    ]


def test_grid_without_color_gives_each_state_its_own_glyph() -> None:
    """Piped stderr and NO_COLOR keep every outcome distinguishable."""
    grid = DiscoveryGrid("srcnet", timeout=10)
    for name, status in [
        ("a", "connected"),
        ("b", "timeout"),
        ("c", "unreachable"),
        ("d", "error"),
        ("e", "pending"),
    ]:
        grid.update(_probe(name, status))

    squares, legend, _ = _render(grid)

    assert squares == "+ ~ x ! ."
    assert legend == (
        "+ 1 discovered   ~ 1 timeout   x 1 unreachable   ! 1 failed   . 1 pending"
    )


@pytest.mark.parametrize(
    ("reports", "expected"),
    [
        (["pending", "connected", "pending"], "connected"),
        (["pending", "connected", "error"], "connected"),
        (["pending", "error", "timeout"], "timeout"),
    ],
    ids=["pending-never-replaces", "connected-wins", "latest-failure"],
)
def test_server_listed_twice_keeps_its_best_state(
    reports: list[str], expected: str
) -> None:
    """A Server listed by several registries shows one best state."""
    grid = DiscoveryGrid("srcnet", timeout=10)
    grid.update(_probe("other", "unreachable"))
    for status in reports:
        grid.update(_probe("canSRC", status))

    grid.finish()

    label = {"connected": "discovered", "timeout": "timeout", "error": "failed"}
    assert f" 1 {label[expected]}" in _render(grid)[1]


def test_finished_grid_summarizes_and_suggests_a_longer_timeout() -> None:
    """Timeouts add the command that waits longer; pending leaves the legend."""
    grid = DiscoveryGrid("srcnet", timeout=10, retry="canfar login srcnet --timeout 20")
    for name, status in [("a", "connected"), ("b", "timeout"), ("c", "error")]:
        grid.update(_probe(name, "pending"))
        grid.update(_probe(name, status))

    grid.finish()

    squares, legend, summary, hint = _render(grid)
    assert squares == "+ ~ !"
    assert legend == "+ 1 discovered   ~ 1 timeout   x 0 unreachable   ! 1 failed"
    assert summary.startswith("Checked 3 servers in ")
    assert summary.endswith("s with a 10s request timeout.")
    assert hint == "1 timed out. To wait longer, run canfar login srcnet --timeout 20"


@pytest.mark.parametrize(
    ("status", "retry"),
    [("unreachable", "canfar login srcnet --timeout 20"), ("timeout", None)],
    ids=["no-timeout", "no-longer-timeout"],
)
def test_finished_grid_omits_hint_without_a_useful_retry(
    status: str, retry: str | None
) -> None:
    """No hint without timeouts, or when the timeout cannot grow."""
    grid = DiscoveryGrid("srcnet", timeout=300, retry=retry)
    grid.update(_probe("a", status))

    grid.finish()

    (summary,) = _render(grid)
    assert summary.startswith("Checked 1 server in ")


def test_single_server_shows_only_progress_summary_and_hint() -> None:
    """One Server needs no squares or legend; a timeout still suggests a retry."""
    grid = DiscoveryGrid("cadc", timeout=10, retry="canfar login cadc --timeout 20")
    grid.update(_probe("canfar", "pending"))

    assert _render(grid) == ["Checking 1 server... 0s"]

    grid.update(_probe("canfar", "timeout"))
    grid.finish()

    summary, hint = _render(grid, color=True)
    assert summary.startswith("Checked 1 server in ")
    assert summary.endswith("s with a 10s request timeout.")
    assert hint == "1 timed out. To wait longer, run canfar login cadc --timeout 20"


def test_stopped_grid_reports_unchecked_servers_without_a_hint() -> None:
    """An interrupted or failed run does not claim it checked every Server."""
    grid = DiscoveryGrid("srcnet", timeout=10, retry="canfar login srcnet --timeout 20")
    for name in ("a", "b", "c"):
        grid.update(_probe(name, "pending"))
    grid.update(_probe("a", "timeout"))

    grid.finish()

    lines = _render(grid)
    assert len(lines) == 3
    assert lines[-1].startswith("Stopped after ")
    assert lines[-1].endswith("s; 2 of 3 servers not checked.")


def test_finished_grid_without_servers_renders_nothing() -> None:
    """A failed registry fetch leaves the error to explain itself."""
    grid = DiscoveryGrid("srcnet", timeout=10)

    grid.finish()

    assert _render(grid) == []


def test_named_grid_labels_squares_in_case_insensitive_name_order() -> None:
    """Verbose discovery labels squares in the order Server lists use."""
    grid = DiscoveryGrid("srcnet", timeout=10, names=True)
    for name, status in [("Zeta", "connected"), ("alpha", "timeout")]:
        grid.update(_probe(name, status))

    assert _render(grid)[0].split() == ["~", "alpha", "+", "Zeta"]


def test_color_grid_uses_outcome_colors_and_a_quiet_hint() -> None:
    """Discovered is green, and the retry hint is grey italic."""
    grid = DiscoveryGrid("srcnet", timeout=10, retry="canfar login srcnet --timeout 20")
    for name, status in [("a", "connected"), ("b", "timeout"), ("c", "error")]:
        grid.update(_probe(name, status))
    grid.finish()

    ansi = _ansi(grid)

    assert "\x1b[32m■" in ansi
    assert "\x1b[33m■" in ansi
    assert "\x1b[31m■" in ansi
    hint = next(line for line in ansi.splitlines() if "timed out" in line)
    assert hint.startswith("\x1b[3;")
