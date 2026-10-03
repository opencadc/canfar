"""Live grid of Science Platform Server discovery for the CLI."""

from __future__ import annotations

import threading
import time
from collections import Counter
from typing import TYPE_CHECKING

from rich.columns import Columns
from rich.text import Text

if TYPE_CHECKING:
    from collections.abc import Iterator

    from rich.console import Console, ConsoleOptions, RenderableType, RenderResult

    from canfar.models.registry import ProbeStatus, ServerProbe

REFRESH_PER_SECOND = 1
"""How often the live grid redraws."""

_STYLES: dict[ProbeStatus, tuple[str, str, str, str]] = {
    "connected": ("■", "+", "green", "discovered"),
    "timeout": ("■", "~", "yellow", "timeout"),
    "unreachable": ("■", "x", "grey42", "unreachable"),
    "error": ("■", "!", "red", "failed"),
    "pending": ("□", ".", "dim", "pending"),
}
"""Square, glyph without color, color, and legend label for each state."""

_RANK: dict[ProbeStatus, int] = {
    "pending": 0,
    "timeout": 1,
    "unreachable": 1,
    "error": 1,
    "connected": 2,
}
"""Which state a Server listed by several registries shows."""


class DiscoveryGrid:
    """Rich renderable that tracks Server discovery as it happens.

    Pass ``update`` as ``discover(on_probe=...)`` and render the grid with
    ``rich.live.Live``. Each Server keeps its square, in Server Name order,
    while its state changes; ``finish`` freezes the elapsed time and replaces
    the progress line with a summary. With a single Server, only the progress
    or summary lines show. Consoles without color, such as piped
    stderr or ``NO_COLOR``, show a distinct glyph per state instead.

    Args:
        idp: Identity Provider whose Servers are discovered.
        timeout: HTTP timeout in seconds for each discovery request.
        names: Label each square with its Server Name.
        retry: Command that retries discovery with a longer timeout, suggested
            when a Server times out.
    """

    def __init__(
        self,
        idp: str,
        *,
        timeout: int,
        names: bool = False,
        retry: str | None = None,
    ) -> None:
        self._idp = idp
        self._timeout = timeout
        self._names = names
        self._retry = retry
        self._lock = threading.Lock()
        self._probes: dict[str, ServerProbe] = {}
        self._started = time.perf_counter()
        self._elapsed: float | None = None

    def update(self, probe: ServerProbe) -> None:
        """Record a Server's discovery state.

        A Server listed by several registries keeps its best state, and a
        ``pending`` report never replaces an outcome.
        """
        with self._lock:
            current = self._probes.get(probe.name)
            if current is None or _RANK[probe.status] >= _RANK[current.status]:
                self._probes[probe.name] = probe

    def finish(self) -> None:
        """Stop the clock and show the summary instead of the progress line."""
        with self._lock:
            if self._elapsed is None:
                self._elapsed = time.perf_counter() - self._started

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        """Render squares, legend, and progress or summary between blank lines."""
        lines = list(self._lines(console))
        if lines:
            yield Text()
            yield from lines
            yield Text()

    def _lines(self, console: Console) -> Iterator[RenderableType]:
        """Yield squares and legend for several Servers, then progress or summary."""
        with self._lock:
            probes = sorted(
                self._probes.values(),
                key=lambda probe: (probe.name.casefold(), probe.name),
            )
            elapsed = self._elapsed
            running = time.perf_counter() - self._started
        if not probes:
            if elapsed is None:
                yield Text(f"Discovering {self._idp} servers... {running:.0f}s", "dim")
            return

        counts = Counter(probe.status for probe in probes)
        if len(probes) > 1:
            mono = console.no_color or console.color_system is None
            yield self._grid(probes, mono=mono)
            yield Text("   ").join(
                Text.assemble(
                    self._glyph(status, mono=mono), f" {counts[status]} {label}"
                )
                for status, (*_, label) in _STYLES.items()
                if status != "pending" or counts[status]
            )
        total = f"{len(probes)} {'server' if len(probes) == 1 else 'servers'}"
        if elapsed is None:
            yield Text(f"Checking {total}... {running:.0f}s", "dim")
        elif counts["pending"]:
            yield Text(
                f"Stopped after {elapsed:.1f}s; {counts['pending']} of {total} "
                "not checked.",
                "dim",
            )
        else:
            yield Text(
                f"Checked {total} in {elapsed:.1f}s with a {self._timeout}s "
                "request timeout.",
                "dim",
            )
            if counts["timeout"] and self._retry is not None:
                yield Text(
                    f"{counts['timeout']} timed out. To wait longer, run {self._retry}",
                    "italic grey50",
                )

    def _grid(self, probes: list[ServerProbe], *, mono: bool) -> RenderableType:
        """Return one square per Server, labelled when names are shown."""
        if not self._names:
            return Text(" ").join(
                self._glyph(probe.status, mono=mono) for probe in probes
            )
        return Columns(
            [
                Text.assemble(
                    self._glyph(probe.status, mono=mono),
                    " ",
                    (probe.name, "" if probe.status == "connected" else "dim"),
                )
                for probe in probes
            ],
            padding=(0, 3),
        )

    @staticmethod
    def _glyph(status: ProbeStatus, *, mono: bool) -> Text:
        """Return the colored square, or the plain glyph, for one state."""
        square, glyph, color, _ = _STYLES[status]
        return Text(glyph) if mono else Text(square, color)
